#!/usr/bin/env python3
"""
DEPRECATED — Use `acw connect` or `python -m cli` instead.

This was the original REPL client prototype. It has been promoted to
a first-class component at cli/ with:
  - Transport abstraction (HTTPTransport + future AgentCoreTransport)
  - Configurable server URL and API key auth
  - Session management (create, resume, list, switch)
  - Integration with the `acw` launcher

This file is kept for reference during the transition period.

Original usage:
    python tools/repl_client.py [--base-url http://localhost:8000] [--profile aws-coworker-test]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import httpx
import asyncio
import itertools

# ── ANSI colors ──────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# ── Spinner ──────────────────────────────────────────────────

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Animated spinner that runs in the background until stopped."""

    def __init__(self, label: str = "Thinking"):
        self._label = label
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self, label: str | None = None):
        if label:
            self._label = label
        if self._task and not self._task.done():
            return  # already running
        self._running = True
        self._task = asyncio.create_task(self._spin())

    async def stop(self):
        """Stop the spinner and wait for it to fully finish before returning."""
        if not self._running and (not self._task or self._task.done()):
            return  # Already stopped — don't clear the line
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        # Clear the spinner line only after the task is fully done
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    async def _spin(self):
        try:
            for frame in itertools.cycle(SPINNER_FRAMES):
                if not self._running:
                    break
                sys.stdout.write(f"\r{DIM}{frame} {self._label}…{RESET}")
                sys.stdout.flush()
                await asyncio.sleep(0.08)
        except asyncio.CancelledError:
            pass
        # No finally cleanup here — stop() handles clearing after awaiting us


def _format_model(model: str) -> str:
    """Format model name to match CLI style: 'haiku' → 'Haiku 4.5'."""
    model_map = {
        "haiku": "Haiku 4.5",
        "sonnet": "Sonnet 4.5",
        "opus": "Opus 4.5",
    }
    return model_map.get(model.lower(), model) if model else ""


def _clean_tool_output(output: str) -> str:
    """
    Clean tool result output — strip raw SDK wrapper dicts and
    agent metadata noise from the output.
    """
    if not output:
        return output

    # Match patterns like {'type': 'text', 'text': '...'} or {"type": "text", "text": "..."}
    # that the SDK wraps tool results in
    cleaned = re.sub(
        r"\{['\"]type['\"]\s*:\s*['\"]text['\"]\s*,\s*['\"]text['\"]\s*:\s*['\"]",
        "",
        output,
    )
    # Remove trailing '} from the above
    cleaned = re.sub(r"['\"]\s*\}\s*$", "", cleaned)
    # Also handle when multiple such blocks appear
    cleaned = re.sub(
        r"['\"]\s*\}\s*\{['\"]type['\"]\s*:\s*['\"]text['\"]\s*,\s*['\"]text['\"]\s*:\s*['\"]",
        "\n",
        cleaned,
    )

    # Strip agentId and usage metadata that leaks from sub-agent results
    # e.g. '} agentId: abc123 (for resuming...)\n<usage>...</usage>
    cleaned = re.sub(
        r"['\"]?\}?\s*agentId:.*$",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    # Strip raw \n<usage>...</usage> blocks
    cleaned = re.sub(
        r"\\n<usage>.*?</usage>",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    # Unescape literal \n to actual newlines for readability
    cleaned = cleaned.replace("\\n", "\n")

    return cleaned.strip()


# ── Markdown → ANSI rendering ────────────────────────────────


def _md_to_ansi(text: str) -> str:
    """
    Convert inline markdown to ANSI terminal formatting.
    Handles: **bold**, `code`, ### headings, --- horizontal rules.
    Applied per-line so it works with streaming (complete lines).
    """
    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.strip()

        # Horizontal rules: ---, ***, ___
        if re.match(r"^[-*_]{3,}\s*$", stripped):
            result.append(f"{DIM}{'─' * 40}{RESET}")
            continue

        # Headings: ## or ### etc.
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            # Apply inline formatting to the heading text too
            heading_text = _md_inline(heading_text)
            if level <= 2:
                result.append(f"{BOLD}{heading_text}{RESET}")
            else:
                result.append(f"{BOLD}{heading_text}{RESET}")
            continue

        # Regular line — apply inline formatting
        result.append(_md_inline(line))

    return "\n".join(result)


def _md_inline(text: str) -> str:
    """Convert inline markdown: **bold**, `code`."""
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", rf"{BOLD}\1{RESET}", text)
    text = re.sub(r"__(.+?)__", rf"{BOLD}\1{RESET}", text)

    # Inline code: `text` → dim rendering
    text = re.sub(r"`([^`]+)`", rf"{CYAN}\1{RESET}", text)

    return text


# ── Table-aware text renderer ────────────────────────────────


class TableRenderer:
    """
    Buffers streaming text to detect markdown tables and render them
    with box-drawing characters. Non-table text passes through immediately.

    Usage:
        renderer = TableRenderer()
        for token in stream:
            output = renderer.feed(token)
            if output:
                sys.stdout.write(output)
        # Flush remaining content
        output = renderer.flush()
        if output:
            sys.stdout.write(output)
    """

    def __init__(self):
        self._line_buf = ""       # Current incomplete line
        self._table_rows = []     # Accumulated table rows
        self._in_table = False
        self._flushed_raw = ""    # Raw text already flushed for current line
        self._was_flushed = False  # Whether current line was partially flushed

    def feed(self, text: str) -> str:
        """Feed streaming text. Returns rendered output to write."""
        output = ""

        for ch in text:
            if ch == "\n":
                # Complete line: combine already-flushed raw text + buffer
                full_line = self._flushed_raw + self._line_buf
                was_flushed = self._was_flushed
                self._line_buf = ""
                self._flushed_raw = ""
                self._was_flushed = False
                output += self._process_line(full_line, was_flushed)
            else:
                self._line_buf += ch

        # For non-table partial lines, flush immediately for smooth streaming.
        # But hold back lines that need full-line context to render:
        #   - Table rows (|...|), headings (#), horizontal rules (---)
        if self._line_buf and not self._in_table:
            s = self._line_buf.lstrip()
            needs_full_line = (
                s.startswith("|")       # table row
                or s.startswith("#")    # heading
                or (len(s) <= 5 and re.match(r"^[-*_]+$", s))  # possible hr
            )
            if not needs_full_line:
                # Flush raw for immediate display — we'll rewrite on newline
                self._flushed_raw += self._line_buf
                self._was_flushed = True
                output += self._line_buf
                self._line_buf = ""

        return output

    def flush(self) -> str:
        """Flush any remaining buffered content."""
        output = ""
        if self._table_rows:
            output += self._render_table()
        if self._line_buf:
            output += _md_to_ansi(self._line_buf)
            self._line_buf = ""
        return output

    def _process_line(self, line: str, was_flushed: bool = False) -> str:
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.endswith("|")
        is_separator = is_table_row and all(
            c in "|-:+ " for c in stripped.replace("|", "")
        )

        if is_table_row:
            if not self._in_table:
                self._in_table = True
            # Skip separator rows (---|---), keep data rows
            if not is_separator:
                self._table_rows.append(stripped)
            return ""
        else:
            output = ""
            if self._in_table:
                output += self._render_table()
                self._in_table = False

            # Detect mid-line headings (e.g., "some text.## Heading")
            # and split into separate lines so the heading renders properly
            heading_mid = re.search(r"(?<=\S)(#{1,4}\s+\S)", line)
            if heading_mid and heading_mid.start() > 0:
                before = line[: heading_mid.start()]
                after = line[heading_mid.start() :]
                if was_flushed:
                    output += f"\r\033[2K{_md_to_ansi(before)}\n"
                else:
                    output += _md_to_ansi(before) + "\n"
                output += _md_to_ansi(after) + "\n"
                return output

            # Apply markdown formatting to the complete line
            formatted = _md_to_ansi(line)

            if was_flushed:
                # We already flushed raw text for this line.
                # Check if markdown formatting changes anything.
                if formatted != line:
                    # Rewrite: carriage return, clear line, write formatted
                    output += f"\r\033[2K{formatted}\n"
                else:
                    # No markdown — just add the newline
                    output += "\n"
            else:
                # Line was held back (heading, table) — emit fully formatted
                output += formatted + "\n"
            return output

    def _render_table(self) -> str:
        if not self._table_rows:
            return ""

        # Parse cells from each row
        parsed: list[list[str]] = []
        for row in self._table_rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            parsed.append(cells)
        self._table_rows = []

        if not parsed:
            return ""

        # Calculate column widths
        num_cols = max(len(row) for row in parsed)
        col_widths = [0] * num_cols
        for row in parsed:
            for i, cell in enumerate(row):
                if i < num_cols:
                    # Strip markdown markers for width calculation
                    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                    plain = re.sub(r"`([^`]+)`", r"\1", plain)
                    col_widths[i] = max(col_widths[i], len(plain))

        # Ensure minimum column width
        col_widths = [max(w, 3) for w in col_widths]

        def h_line(left: str, mid: str, right: str) -> str:
            parts = [left]
            for i, w in enumerate(col_widths):
                parts.append("─" * (w + 2))
                if i < num_cols - 1:
                    parts.append(mid)
            parts.append(right)
            return "".join(parts) + "\n"

        def data_row(cells: list[str]) -> str:
            parts = ["│"]
            for i in range(num_cols):
                cell = cells[i] if i < len(cells) else ""
                # Calculate display width (strip markdown for padding)
                plain = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                plain = re.sub(r"`([^`]+)`", r"\1", plain)
                pad = col_widths[i] - len(plain)
                # Render markdown in cell content
                rendered_cell = _md_inline(cell)
                parts.append(f" {rendered_cell}{' ' * pad} ")
                parts.append("│")
            return "".join(parts) + "\n"

        # Build the table
        output = h_line("┌", "┬", "┐")
        for idx, row in enumerate(parsed):
            output += data_row(row)
            if idx == 0 and len(parsed) > 1:
                # Separator after header row
                output += h_line("├", "┼", "┤")
        output += h_line("└", "┴", "┘")

        return output


def _truncate_lines(text: str, max_lines: int = 8) -> str:
    """Truncate multi-line text, showing first N lines + count."""
    lines = text.strip().split("\n")
    if len(lines) <= max_lines:
        return "\n      ".join(lines)
    preview = "\n      ".join(lines[:max_lines])
    return f"{preview}\n      {DIM}... ({len(lines)} lines total){RESET}{GREEN}"


def render_event(data: dict) -> str | None:
    """Render a single SSE event as a formatted terminal line."""
    etype = data.get("type", "unknown")

    if etype == "session_info":
        profile = data.get("profile", "?")
        region = data.get("region", "?")
        return f"{BLUE}ℹ Profile: {BOLD}{profile}{RESET}{BLUE}  Region: {region}{RESET}"

    if etype == "message":
        # Handled inline in stream_message for smooth rendering
        return None

    if etype == "tool_use":
        tool = data.get("tool", "?")
        inp = data.get("input", {})
        status = data.get("status", "")

        # Skip 'starting' events from StreamEvent content_block_start
        # (we'll show the full tool_use from AssistantMessage instead)
        if status == "starting":
            return None

        if tool == "Skill":
            skill_name = inp.get("skill", inp.get("name", "?"))
            return f"{CYAN}⏺ Skill(/{skill_name}){RESET}\n{GREEN}  ⎿  Successfully loaded skill{RESET}"
        elif tool == "Task":
            # Prefer 'description' over 'prompt' for cleaner display
            desc = inp.get("description", "")
            if not desc:
                # Fall back to first line of prompt, skip agent identity preamble
                prompt = inp.get("prompt", "?")
                first_line = prompt.split("\n")[0][:80]
                # Strip common preambles like "You are acting as..."
                if first_line.startswith("You are acting as"):
                    desc = first_line.replace("You are acting as ", "").rstrip(".")
                else:
                    desc = first_line
            else:
                desc = desc[:80]
            model = inp.get("model", "")
            model_str = f" {_format_model(model)}" if model else ""
            return f"{CYAN}⏺ Task({desc}){model_str}{RESET}"
        elif tool == "Bash":
            cmd = inp.get("command", "?")
            desc = inp.get("description", "")
            label = desc if desc else (cmd[:80] if len(cmd) <= 80 else cmd[:77] + "...")
            return f"{CYAN}⏺ Bash({label}){RESET}"
        elif tool == "Read":
            path = inp.get("file_path", "?")
            return f"{CYAN}⏺ Read({path}){RESET}"
        elif tool == "Write":
            path = inp.get("file_path", "?")
            return f"{CYAN}⏺ Write({path}){RESET}"
        elif tool == "Edit":
            path = inp.get("file_path", "?")
            return f"{CYAN}⏺ Edit({path}){RESET}"
        elif tool == "Grep":
            pattern = inp.get("pattern", "?")
            return f"{CYAN}⏺ Grep({pattern}){RESET}"
        elif tool == "Glob":
            pattern = inp.get("pattern", "?")
            return f"{CYAN}⏺ Glob({pattern}){RESET}"
        elif tool == "TodoWrite":
            return None  # Skip — we show todo_update instead
        else:
            summary = json.dumps(inp)
            if len(summary) > 60:
                summary = summary[:57] + "..."
            return f"{CYAN}⏺ {tool}({summary}){RESET}"

    if etype == "tool_result":
        output = data.get("output", "")
        error = data.get("error")

        # Suppress skill-loading results (we already show "Successfully loaded skill")
        if output and ("launching skill" in output.lower()
                       or "successfully loaded skill" in output.lower()
                       or "skill is loading" in output.lower()):
            return None

        if error:
            cleaned = _clean_tool_output(error)
            return f"{RED}  ⎿ Error: {cleaned[:200]}{RESET}"
        if not output.strip():
            return None
        cleaned = _clean_tool_output(output)
        truncated = _truncate_lines(cleaned)
        return f"{GREEN}  ⎿ {truncated}{RESET}"

    if etype == "sub_agent_spawn":
        model = data.get("model", "?")
        task = data.get("task", "")
        # Truncate long agent prompts to just the first meaningful line
        first_line = task.split("\n")[0][:80]
        # Strip common preambles
        if first_line.startswith("You are acting as"):
            first_line = first_line.replace("You are acting as ", "").rstrip(".")
        model_display = _format_model(model)
        return f"{CYAN}⏺ Task({first_line}) {model_display}{RESET}"

    if etype == "sub_agent_complete":
        tool_uses = data.get("tool_uses", 0)
        tokens = data.get("tokens", 0)
        duration = data.get("duration", 0)
        parts = []
        if tool_uses:
            parts.append(f"{tool_uses} tool use{'s' if tool_uses != 1 else ''}")
        if tokens:
            if tokens >= 1000:
                parts.append(f"{tokens / 1000:.1f}k tokens")
            else:
                parts.append(f"{tokens} tokens")
        if duration > 0:
            if duration >= 1000:
                parts.append(f"{duration / 1000:.0f}s")
            else:
                parts.append(f"{duration}ms")
        summary = " · ".join(parts) if parts else data.get("status", "done")
        return f"{DIM}  ⎿  Done ({summary}){RESET}"

    if etype == "permission_request":
        action = data.get("action", "?")
        desc = data.get("description", "")
        return f"{YELLOW}⚠ Permission needed: {action} — {desc}{RESET}"

    if etype == "error":
        msg = data.get("message", "?")
        severity = data.get("severity", "error")
        return f"{RED}✗ [{severity}] {msg}{RESET}"

    if etype == "todo_update":
        todos = data.get("todos", [])
        if not todos:
            return None
        lines = []
        for t in todos:
            s = t.get("status", "")
            icon = {"pending": "○", "in_progress": "◉", "completed": "✓"}.get(s, "?")
            color = {"pending": DIM, "in_progress": YELLOW, "completed": GREEN}.get(s, "")
            lines.append(f"  {color}{icon} {t.get('content', '?')}{RESET}")
        return f"{DIM}📋 Todos:{RESET}\n" + "\n".join(lines)

    if etype == "execution_complete":
        duration = data.get("duration", 0)
        events = data.get("eventCount", 0)
        agents = data.get("agentsSpawned", 0)
        err_count = data.get("errors", 0)

        # Format duration nicely
        if duration > 1000:
            dur_str = f"{duration / 1000:.1f}s"
        else:
            dur_str = f"{duration}ms"

        parts = [dur_str]
        if agents:
            parts.append(f"{agents} agent{'s' if agents != 1 else ''}")
        if err_count:
            parts.append(f"{RED}{err_count} error{'s' if err_count != 1 else ''}{RESET}{DIM}")
        parts.append(f"{events} events")

        bar = "─" * 60
        return f"{DIM}{bar}\n  {', '.join(parts)}{RESET}"

    # Unknown event type — show raw for debugging
    return f"{DIM}[{etype}] {json.dumps(data)[:120]}{RESET}"


async def stream_message(client: httpx.AsyncClient, base_url: str, session_id: str, content: str):
    """Send a message and stream SSE events to the terminal."""
    url = f"{base_url}/api/sessions/{session_id}/messages/stream"

    # Track state for smooth text rendering
    in_text = False      # Are we currently printing streaming text?
    pending_ws = ""      # Buffered whitespace before visible text arrives
    table = TableRenderer()  # Detects and renders markdown tables
    spinner = Spinner("Thinking")
    spinner.start()

    async with client.stream(
        "POST",
        url,
        json={"content": content},
        timeout=300.0,
    ) as response:
        if response.status_code != 200:
            await spinner.stop()
            body = await response.aread()
            print(f"{RED}Error {response.status_code}: {body.decode()}{RESET}")
            return

        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk

            # Parse SSE messages from buffer
            while "\n\n" in buffer:
                msg, buffer = buffer.split("\n\n", 1)

                # Extract data lines
                data_line = None
                for line in msg.strip().split("\n"):
                    if line.startswith("data: "):
                        data_line = line[6:]

                if not data_line:
                    continue

                try:
                    data = json.loads(data_line)
                except json.JSONDecodeError:
                    continue

                etype = data.get("type", "")

                # Handle streaming text deltas inline
                if etype == "message":
                    delta = data.get("delta", True)
                    text = data.get("content", "")
                    if delta and text:
                        if not in_text and text.strip() == "":
                            # Buffer whitespace until we see real text —
                            # keeps the spinner visible during blank lines
                            pending_ws += text
                        else:
                            await spinner.stop()
                            if not in_text:
                                # Flush any buffered whitespace now that
                                # real text has arrived (skip leading newlines)
                                pending_ws = pending_ws.lstrip("\n")
                                if pending_ws:
                                    sys.stdout.write(pending_ws)
                                pending_ws = ""
                            in_text = True
                            rendered_text = table.feed(text)
                            if rendered_text:
                                sys.stdout.write(rendered_text)
                                sys.stdout.flush()
                    # Non-delta (final complete) messages — skip
                    continue

                # For non-message events, check if it renders to anything
                rendered = render_event(data)

                if rendered:
                    # End any in-progress text line before printing event
                    if in_text:
                        # Flush any buffered table content
                        remaining = table.flush()
                        if remaining:
                            sys.stdout.write(remaining)
                        print()
                        in_text = False
                    pending_ws = ""  # Discard buffered whitespace
                    await spinner.stop()
                    print(rendered)
                    # Restart spinner while waiting for next content
                    if etype not in ("execution_complete",):
                        spinner.start("Working")

                elif etype == "execution_complete":
                    if in_text:
                        remaining = table.flush()
                        if remaining:
                            sys.stdout.write(remaining)
                        print()
                        in_text = False
                    await spinner.stop()

                # Non-rendered events: don't print newlines, don't touch spinner

    # Clean up
    remaining = table.flush()
    if remaining:
        sys.stdout.write(remaining)
    await spinner.stop()
    if in_text:
        print()


async def create_session(client: httpx.AsyncClient, base_url: str, profile: str, region: str) -> str:
    """Create a new session and return its ID."""
    resp = await client.post(
        f"{base_url}/api/sessions",
        json={"profile": profile, "region": region},
    )
    resp.raise_for_status()
    data = resp.json()
    return data["id"]


async def main():
    parser = argparse.ArgumentParser(description="AWS Coworker REPL Client")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Server base URL")
    parser.add_argument("--profile", default="", help="AWS profile name")
    parser.add_argument("--region", default="", help="AWS region")
    parser.add_argument("--session-id", default="", help="Resume existing session")
    args = parser.parse_args()

    print(f"{BOLD}AWS Coworker REPL{RESET}")
    print(f"{DIM}Server: {args.base_url}{RESET}")
    print(f"{DIM}Type 'exit' or Ctrl+C to quit{RESET}")
    print()

    async with httpx.AsyncClient() as client:
        # Check server health
        try:
            resp = await client.get(f"{args.base_url}/health", timeout=5.0)
            if resp.status_code != 200:
                print(f"{RED}Server not responding at {args.base_url}{RESET}")
                return
            print(f"{GREEN}Connected to server{RESET}")
        except httpx.ConnectError:
            print(f"{RED}Cannot connect to {args.base_url} — is the server running?{RESET}")
            return

        # Create or resume session
        if args.session_id:
            session_id = args.session_id
            print(f"{DIM}Resuming session: {session_id}{RESET}")
        else:
            session_id = await create_session(client, args.base_url, args.profile, args.region)
            profile_display = args.profile or "(default)"
            region_display = args.region or "(default)"
            print(f"{DIM}Session: {session_id}  Profile: {profile_display}  Region: {region_display}{RESET}")

        print(f"{DIM}{'─' * 60}{RESET}")
        print()

        # REPL loop
        while True:
            try:
                user_input = input(f"{BOLD}❯ {RESET}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n{DIM}Goodbye.{RESET}")
                break

            user_input = user_input.strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print(f"{DIM}Goodbye.{RESET}")
                break

            print()
            await stream_message(client, args.base_url, session_id, user_input)
            print()


if __name__ == "__main__":
    asyncio.run(main())
