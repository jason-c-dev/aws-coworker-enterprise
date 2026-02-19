"""
Claude Agent SDK wrapper.

Wraps ClaudeSDKClient to provide:
- Session-scoped SDK instances
- Event translation (SDK events → our SSE event types)
- Permission callback integration
- Streaming support

NOTE: This is the integration layer. Until the Claude Agent SDK is installed
and configured, this module provides a mock implementation that returns
placeholder responses. The mock allows the full API to be tested end-to-end
without requiring SDK credentials.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, AsyncGenerator

from .event_stream import (
    execution_complete_event,
    message_event,
    session_info_event,
    format_sse,
)

logger = logging.getLogger(__name__)

# Flag: set to True when claude-code-sdk is available
SDK_AVAILABLE = False

try:
    from claude_code_sdk import ClaudeSDKClient, ClaudeAgentOptions
    SDK_AVAILABLE = True
    logger.info("Claude Agent SDK available")
except ImportError:
    logger.warning(
        "Claude Agent SDK not installed. Running in mock mode. "
        "Install with: pip install claude-code-sdk"
    )


class SDKClientWrapper:
    """
    Wrapper around ClaudeSDKClient (or mock) for a single session.

    Provides:
    - send_message(content) → AsyncGenerator of SSE events
    - close() to clean up
    """

    def __init__(
        self,
        session_id: str,
        project_root: str,
        profile: str = "",
        region: str = "",
    ) -> None:
        self.session_id = session_id
        self.project_root = project_root
        self.profile = profile
        self.region = region
        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the SDK client. Called lazily on first message."""
        if self._initialized:
            return

        if SDK_AVAILABLE:
            try:
                options = ClaudeAgentOptions(
                    system_prompt={"type": "preset", "preset": "claude_code"},
                    setting_sources=["project"],
                    cwd=self.project_root,
                )
                self._client = ClaudeSDKClient(options=options)
                await self._client.__aenter__()
                self._initialized = True
                logger.info(f"SDK client initialized for session {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to initialize SDK client: {e}")
                self._initialized = True  # Don't retry
        else:
            self._initialized = True
            logger.info(f"Mock SDK client for session {self.session_id}")

    async def send_message(self, content: str) -> AsyncGenerator[str, None]:
        """
        Send a message and yield SSE-formatted events.

        Each yielded string is a complete SSE message ready for the stream.
        """
        await self.initialize()

        start_time = time.time()
        event_count = 0

        # Emit session info
        info = session_info_event(
            profile=self.profile or "default",
            region=self.region or "us-east-1",
        )
        event_count += 1
        yield format_sse(info)

        if SDK_AVAILABLE and self._client:
            # Real SDK path — translate SDK events to our SSE format
            # TODO: Implement full SDK event translation when SDK is available
            # For now, fall through to mock
            pass

        # Mock implementation: simulate a response
        mock_response = (
            f"[Mock Response] I received your message: \"{content}\"\n\n"
            f"The Claude Agent SDK is not yet connected. This is a mock response "
            f"to verify the API pipeline works end-to-end.\n\n"
            f"Session: {self.session_id}\n"
            f"Profile: {self.profile or 'default'}\n"
            f"Region: {self.region or 'us-east-1'}"
        )

        # Stream the response in chunks
        words = mock_response.split(" ")
        chunks = []
        current = []
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
            await asyncio.sleep(0.05)  # Simulate streaming delay

        # Final complete message
        evt = message_event(content=mock_response, delta=False)
        event_count += 1
        yield format_sse(evt)

        # Execution complete
        duration = int((time.time() - start_time) * 1000)
        complete = execution_complete_event(
            event_count=event_count,
            duration=duration,
            summary="Mock response completed",
        )
        yield format_sse(complete)

    async def close(self) -> None:
        """Clean up the SDK client."""
        if self._client and SDK_AVAILABLE:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing SDK client: {e}")
        self._client = None
        self._initialized = False
