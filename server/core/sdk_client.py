"""
Claude Agent SDK wrapper.

Wraps the Claude Agent SDK's ClaudeSDKClient to provide:
- Session-scoped SDK instances with multi-turn conversation support
- Event translation (SDK message types → our SSE event types)
- Streaming support for real-time SSE

Architecture:
  The SDK's ClaudeSDKClient must live in a single async context for its
  entire lifetime (it uses anyio task groups internally). HTTP requests
  arrive in separate async contexts. To bridge this gap, the SDK client
  runs in a persistent background task that communicates via asyncio.Queues:

    HTTP Request  ──→  prompt_queue  ──→  Background Task (owns SDK)
                                                  ↓
    HTTP Request  ←──  event_queue   ←──  query() + receive_response()

When the SDK is not installed, falls back to a mock that returns
placeholder responses so the full API pipeline can be tested.

Requires:
  pip install claude-agent-sdk
  Claude Code CLI: npm install -g @anthropic-ai/claude-code
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator

from .event_stream import (
    error_event,
    execution_complete_event,
    format_sse,
    message_event,
    session_info_event,
    sub_agent_spawn_event,
    tool_result_event,
    tool_use_event,
)

logger = logging.getLogger(__name__)

# ── SDK availability + monkey-patch ─────────────────────────────

SDK_AVAILABLE = False
STREAM_EVENTS_AVAILABLE = False
StreamEvent = None  # Will be set if SDK supports it
_FORCE_MOCK = os.getenv("ACW_FORCE_MOCK", "").lower() in ("1", "true", "yes")

# Sentinel to signal the background task to shut down
_SHUTDOWN = object()

# Sentinel to signal end of events for one turn
_TURN_DONE = object()


@dataclass
class _UnknownMessage:
    """Placeholder for SDK message types we don't recognize."""
    raw_type: str
    data: dict


def _patch_sdk_parser():
    """
    Monkey-patch the SDK's message parser so unknown message types
    (rate_limit_event, tool_use_summary, etc.) return an _UnknownMessage
    instead of raising MessageParseError.

    This lets us use the normal public receive_response() API without
    it crashing on events the SDK doesn't know about yet.
    """
    try:
        from claude_agent_sdk._internal import message_parser
        from claude_agent_sdk._errors import MessageParseError

        _original = message_parser.parse_message

        def _safe_parse(data: dict):
            try:
                return _original(data)
            except MessageParseError:
                msg_type = data.get("type", "unknown")
                logger.debug(f"Skipping unknown SDK message type: {msg_type}")
                return _UnknownMessage(raw_type=msg_type, data=data)

        message_parser.parse_message = _safe_parse
        logger.info("Patched SDK message parser to handle unknown types")
    except Exception as e:
        logger.warning(f"Could not patch SDK message parser: {e}")


if _FORCE_MOCK:
    logger.info("Mock mode forced via ACW_FORCE_MOCK environment variable")
else:
    try:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ClaudeSDKClient,
            ResultMessage,
            SystemMessage,
            TextBlock,
            ToolResultBlock,
            ToolUseBlock,
            UserMessage,
        )

        SDK_AVAILABLE = True
        _patch_sdk_parser()
        logger.info("Claude Agent SDK available")

        # StreamEvent may be in claude_agent_sdk.types rather than the top-level
        # Try multiple import paths
        try:
            from claude_agent_sdk import StreamEvent
            STREAM_EVENTS_AVAILABLE = True
            logger.info("StreamEvent available (top-level import) — token-level streaming enabled")
        except ImportError:
            try:
                from claude_agent_sdk.types import StreamEvent
                STREAM_EVENTS_AVAILABLE = True
                logger.info("StreamEvent available (from .types) — token-level streaming enabled")
            except ImportError:
                StreamEvent = None  # type: ignore
                STREAM_EVENTS_AVAILABLE = False
                logger.info("StreamEvent not found in SDK — using batched message streaming")

    except ImportError as e:
        logger.warning(
            "Claude Agent SDK not installed. Running in mock mode. "
            f"Install with: pip install claude-agent-sdk (error: {e})"
        )


# ── Background task that owns the SDK client ──────────────────


async def _sdk_background_loop(
    prompt_queue: asyncio.Queue,
    event_queue: asyncio.Queue,
    project_root: str,
    profile: str,
    region: str,
    allowed_tools: list[str],
    session_id: str,
):
    """
    Long-lived background task that owns the ClaudeSDKClient.

    Waits for prompts on prompt_queue, runs query() + receive_response(),
    and pushes SSE event dicts onto event_queue. Sends _TURN_DONE after
    each turn completes. Exits when it receives _SHUTDOWN.
    """
    env: dict[str, str] = {"CLAUDECODE": ""}
    if profile:
        env["AWS_PROFILE"] = profile
    if region:
        env["AWS_REGION"] = region

    opts_kwargs: dict[str, Any] = dict(
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["project"],
        cwd=project_root,
        allowed_tools=allowed_tools,
        permission_mode="bypassPermissions",
        env=env,
    )
    # Only request partial messages if StreamEvent is available to consume them
    if STREAM_EVENTS_AVAILABLE:
        opts_kwargs["include_partial_messages"] = True

    try:
        options = ClaudeAgentOptions(**opts_kwargs)
    except TypeError as e:
        # If include_partial_messages isn't supported by this SDK version,
        # fall back without it
        logger.warning(f"ClaudeAgentOptions rejected kwargs, retrying without include_partial_messages: {e}")
        opts_kwargs.pop("include_partial_messages", None)
        options = ClaudeAgentOptions(**opts_kwargs)

    try:
        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"[{session_id}] SDK background task started")

            while True:
                # Wait for next prompt (or shutdown)
                prompt = await prompt_queue.get()

                if prompt is _SHUTDOWN:
                    logger.info(f"[{session_id}] SDK background task shutting down")
                    break

                # Process one turn
                try:
                    await client.query(prompt)

                    async for msg in client.receive_response():
                        await event_queue.put(msg)

                except Exception as e:
                    logger.error(f"[{session_id}] SDK error during turn: {e}", exc_info=True)
                    await event_queue.put(("error", str(e)))

                # Signal turn complete
                await event_queue.put(_TURN_DONE)

    except Exception as e:
        logger.error(f"[{session_id}] SDK background task crashed: {e}", exc_info=True)
        # Push error + done so any waiting caller unblocks
        await event_queue.put(("error", f"SDK process crashed: {e}"))
        await event_queue.put(_TURN_DONE)


# ── SDK Client Wrapper ──────────────────────────────────────────


class SDKClientWrapper:
    """
    Wrapper around ClaudeSDKClient (or mock) for a single session.

    Provides:
    - send_message(content) → AsyncGenerator of SSE events
    - close() to clean up

    The SDK client lives in a persistent background task to ensure it
    stays in a single async context across multiple HTTP requests.
    """

    def __init__(
        self,
        session_id: str,
        project_root: str,
        profile: str = "",
        region: str = "",
        allowed_tools: list[str] | None = None,
        permission_handler: Any | None = None,
    ) -> None:
        self.session_id = session_id
        self.project_root = project_root
        self.profile = profile
        self.region = region
        self.allowed_tools = allowed_tools or [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "TodoWrite",
        ]
        self.permission_handler = permission_handler

        # Communication queues with the background task
        self._prompt_queue: asyncio.Queue = asyncio.Queue()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._bg_task: asyncio.Task | None = None
        self._initialized = False

    async def _ensure_started(self) -> None:
        """Start the background task if not already running."""
        if self._initialized:
            return

        if SDK_AVAILABLE:
            self._bg_task = asyncio.create_task(
                _sdk_background_loop(
                    prompt_queue=self._prompt_queue,
                    event_queue=self._event_queue,
                    project_root=self.project_root,
                    profile=self.profile,
                    region=self.region,
                    allowed_tools=self.allowed_tools,
                    session_id=self.session_id,
                ),
                name=f"sdk-{self.session_id}",
            )
            logger.info(f"Started SDK background task for session {self.session_id}")

        self._initialized = True

    def _translate_message(self, msg: Any) -> list[dict]:
        """
        Translate a single SDK message into one or more SSE event dicts.
        Returns a list because one SDK message can produce multiple events.
        """
        events = []

        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    if STREAM_EVENTS_AVAILABLE:
                        # With include_partial_messages=True, we get token-level
                        # text via StreamEvent. AssistantMessage TextBlocks are
                        # the accumulated text — skip to avoid duplication.
                        events.append(("_text_block", block.text))
                    else:
                        # Without StreamEvent, AssistantMessage is our only
                        # source of text — emit it as a delta.
                        if block.text:
                            events.append(message_event(content=block.text, delta=True))
                elif isinstance(block, ToolUseBlock):
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}

                    if tool_name == "Task":
                        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
                        task_desc = ""
                        model = "haiku"
                        if isinstance(tool_input, dict):
                            task_desc = tool_input.get("prompt", tool_input.get("description", ""))
                            model = tool_input.get("model", "haiku")
                        events.append(sub_agent_spawn_event(
                            agent_id=agent_id,
                            agent_name=tool_input.get("subagent_type", "general-purpose") if isinstance(tool_input, dict) else "general-purpose",
                            model=model,
                            task=task_desc[:200],
                        ))
                    else:
                        events.append(tool_use_event(
                            tool=tool_name,
                            input_data=tool_input if isinstance(tool_input, dict) else {"raw": str(tool_input)},
                            status="started",
                        ))

        elif isinstance(msg, ResultMessage):
            result_text = getattr(msg, "result", None)
            if result_text:
                events.append(("result_text", result_text))

            logger.info(
                f"SDK complete: turns={getattr(msg, 'num_turns', '?')}, "
                f"cost=${getattr(msg, 'total_cost_usd', 0) or 0:.4f}, "
                f"duration={getattr(msg, 'duration_ms', 0)}ms"
            )

        elif isinstance(msg, UserMessage):
            msg_content = msg.content
            if isinstance(msg_content, list):
                for block in msg_content:
                    if isinstance(block, ToolResultBlock):
                        tool_id = getattr(block, "tool_use_id", f"tu-{uuid.uuid4().hex[:8]}")
                        output_text = ""
                        if hasattr(block, "content"):
                            if isinstance(block.content, str):
                                output_text = block.content
                            elif isinstance(block.content, list):
                                output_text = " ".join(
                                    getattr(b, "text", str(b)) for b in block.content
                                )
                        error_text = None
                        if getattr(block, "is_error", False):
                            error_text = output_text
                        events.append(tool_result_event(
                            tool_use_id=tool_id,
                            tool="",
                            output=output_text[:2000],
                            error=error_text,
                        ))

        elif STREAM_EVENTS_AVAILABLE and StreamEvent is not None and isinstance(msg, StreamEvent):
            # Raw Claude API stream event — gives us token-level streaming
            raw = msg.event
            event_type = raw.get("type", "")

            if event_type == "content_block_delta":
                delta = raw.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        events.append(message_event(content=text, delta=True))

            elif event_type == "content_block_start":
                cb = raw.get("content_block", {})
                if cb.get("type") == "tool_use":
                    tool_name = cb.get("name", "")
                    tool_id = cb.get("id", "")
                    # We'll get the full input later via AssistantMessage,
                    # but emit an early tool_use event for responsiveness
                    events.append(tool_use_event(
                        tool=tool_name,
                        input_data={"id": tool_id},
                        status="starting",
                    ))

            # Other stream event types (message_start, message_delta,
            # content_block_stop, message_stop) are metadata — skip them
            # to avoid noise.

        elif isinstance(msg, SystemMessage):
            logger.debug(f"SDK system message: subtype={getattr(msg, 'subtype', '?')}")

        elif isinstance(msg, _UnknownMessage):
            logger.debug(f"Skipped unknown SDK event: {msg.raw_type}")

        else:
            logger.debug(f"Unhandled SDK message type: {type(msg).__name__}")

        return events

    async def send_message(self, content: str) -> AsyncGenerator[str, None]:
        """
        Send a message and yield SSE-formatted events.

        Pushes the prompt to the background task via queue, then reads
        translated events back until _TURN_DONE.
        """
        await self._ensure_started()

        start_time = time.time()
        event_count = 0
        agents_spawned = 0
        errors = 0

        # Emit session info
        info = session_info_event(
            profile=self.profile or "default",
            region=self.region or "us-east-1",
        )
        event_count += 1
        yield format_sse(info)

        if SDK_AVAILABLE and self._bg_task is not None:
            # ── Real SDK path via background task ───────────────
            full_text = ""

            # Sub-agent depth tracking: when the orchestrator spawns a
            # sub-agent via the Task tool, the SDK (with include_partial_messages)
            # yields the sub-agent's messages through receive_response() too.
            # We must suppress sub-agent text to avoid duplicating the
            # orchestrator's output. Tool events (tool_use, tool_result,
            # sub_agent_spawn) still pass through.
            sub_agent_depth = 0
            task_tool_use_ids: set[str] = set()

            # Check if background task is still alive
            if self._bg_task.done():
                exc = self._bg_task.exception() if not self._bg_task.cancelled() else None
                err_msg = f"SDK background task is not running: {exc}" if exc else "SDK background task exited"
                logger.error(err_msg)
                evt = error_event(severity="error", source="sdk", message=err_msg, recoverable=False)
                event_count += 1
                yield format_sse(evt)
            else:
                # Send prompt to background task
                await self._prompt_queue.put(content)

                # Read events until turn is done
                try:
                    while True:
                        item = await asyncio.wait_for(self._event_queue.get(), timeout=300)

                        if item is _TURN_DONE:
                            break

                        # Handle error tuples from the background task
                        if isinstance(item, tuple) and len(item) == 2 and item[0] == "error":
                            errors += 1
                            evt = error_event(
                                severity="error",
                                source="sdk",
                                message=item[1],
                                recoverable=True,
                            )
                            event_count += 1
                            yield format_sse(evt)
                            continue

                        # ── Track sub-agent depth from raw SDK messages ──
                        # We inspect the raw message BEFORE translation to
                        # know whether we're inside a sub-agent conversation.
                        if isinstance(item, AssistantMessage):
                            for block in item.content:
                                if isinstance(block, ToolUseBlock) and block.name == "Task":
                                    tool_id = getattr(block, "id", None)
                                    if tool_id:
                                        task_tool_use_ids.add(tool_id)
                                    sub_agent_depth += 1
                                    logger.debug(f"Sub-agent depth++ → {sub_agent_depth}")
                        elif isinstance(item, UserMessage) and isinstance(item.content, list):
                            for block in item.content:
                                if isinstance(block, ToolResultBlock):
                                    result_id = getattr(block, "tool_use_id", None)
                                    if result_id in task_tool_use_ids:
                                        task_tool_use_ids.discard(result_id)
                                        sub_agent_depth = max(0, sub_agent_depth - 1)
                                        logger.debug(f"Sub-agent depth-- → {sub_agent_depth}")

                        # Translate SDK message to SSE events
                        translated = self._translate_message(item)
                        for evt in translated:
                            # Special case: result_text from ResultMessage
                            if isinstance(evt, tuple) and evt[0] == "result_text":
                                result_text = evt[1]
                                if STREAM_EVENTS_AVAILABLE:
                                    # StreamEvent tokens already delivered all text
                                    # to the client — skip to avoid duplication.
                                    continue
                                if result_text and result_text not in full_text:
                                    full_text += result_text
                                    sse_evt = message_event(content=result_text, delta=True)
                                    event_count += 1
                                    yield format_sse(sse_evt)
                                continue

                            # Special case: _text_block from AssistantMessage
                            # (accumulated text — don't emit since StreamEvent
                            # already sent tokens. Don't add to full_text either,
                            # as the StreamEvent deltas already accumulate there.
                            # Adding both would corrupt full_text with duplicates,
                            # causing the result_text dedup check to fail.)
                            if isinstance(evt, tuple) and evt[0] == "_text_block":
                                continue

                            # Suppress sub-agent text: when inside a sub-agent
                            # (depth > 0), the SDK yields the sub-agent's
                            # StreamEvent text deltas through receive_response().
                            # These must not be emitted as orchestrator text.
                            # Tool events (tool_use, tool_result, sub_agent_spawn)
                            # still pass through — only text is suppressed.
                            if sub_agent_depth > 0:
                                evt_type = evt.get("type", "")
                                if evt_type == "message" and evt.get("delta"):
                                    continue

                            # Track stats
                            if evt.get("type") == "sub_agent_spawn":
                                agents_spawned += 1
                            if evt.get("error"):
                                errors += 1

                            # Check for text content to accumulate
                            if evt.get("type") == "message" and evt.get("delta"):
                                full_text += evt.get("content", "")

                            event_count += 1
                            yield format_sse(evt)

                except asyncio.TimeoutError:
                    errors += 1
                    evt = error_event(
                        severity="error",
                        source="sdk",
                        message="Response timed out after 300 seconds",
                        recoverable=True,
                    )
                    event_count += 1
                    yield format_sse(evt)

                except Exception as e:
                    logger.error(f"Error reading SDK events: {e}", exc_info=True)
                    errors += 1
                    evt = error_event(
                        severity="error",
                        source="sdk",
                        message=str(e),
                        recoverable=True,
                    )
                    event_count += 1
                    yield format_sse(evt)

                # Emit final non-delta message
                if full_text:
                    evt = message_event(content=full_text, delta=False)
                    event_count += 1
                    yield format_sse(evt)

        else:
            # ── Mock implementation ────────────────────────────
            mock_response = (
                f"**[Mock Response]** I received your message: \"{content}\"\n\n"
                f"The Claude Agent SDK is not connected. This is a mock response "
                f"to verify the API pipeline works end-to-end.\n\n"
                f"- Session: `{self.session_id}`\n"
                f"- Profile: `{self.profile or 'default'}`\n"
                f"- Region: `{self.region or 'us-east-1'}`"
            )

            # Simulate a tool use
            tu_id = f"tu-{uuid.uuid4().hex[:8]}"
            evt = tool_use_event(
                tool="Read",
                input_data={"file_path": "CLAUDE.md"},
                status="started",
            )
            event_count += 1
            yield format_sse(evt)
            await asyncio.sleep(0.1)

            evt = tool_result_event(
                tool_use_id=tu_id,
                tool="Read",
                output="[Mock] CLAUDE.md contents...",
            )
            event_count += 1
            yield format_sse(evt)

            # Stream the response in chunks
            words = mock_response.split(" ")
            chunks: list[str] = []
            current: list[str] = []
            for word in words:
                current.append(word)
                if len(current) >= 5:
                    chunks.append(" ".join(current) + " ")
                    current = []
            if current:
                chunks.append(" ".join(current))

            for chunk in chunks:
                evt = message_event(content=chunk, delta=True)
                event_count += 1
                yield format_sse(evt)
                await asyncio.sleep(0.05)

            # Final complete message
            evt = message_event(content=mock_response, delta=False)
            event_count += 1
            yield format_sse(evt)

        # Execution complete summary
        duration = int((time.time() - start_time) * 1000)
        complete = execution_complete_event(
            event_count=event_count,
            duration=duration,
            agents_spawned=agents_spawned,
            errors=errors,
            summary="SDK response completed" if SDK_AVAILABLE and self._bg_task else "Mock response completed",
        )
        yield format_sse(complete)

    async def close(self) -> None:
        """Clean up the SDK client and background task."""
        if self._bg_task and not self._bg_task.done():
            # Signal shutdown
            await self._prompt_queue.put(_SHUTDOWN)
            try:
                await asyncio.wait_for(self._bg_task, timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"SDK background task didn't stop gracefully, cancelling")
                self._bg_task.cancel()
                try:
                    await self._bg_task
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                logger.warning(f"Error closing SDK background task: {e}")

        self._bg_task = None
        self._initialized = False
        logger.info(f"SDK client closed for session {self.session_id}")
