"""
Terminal rendering for ACW CLI.

Handles: ANSI colours, markdown-to-terminal conversion, box-drawn tables,
animated spinner, and SSE event formatting.

Extracted from the rendering logic in the original tools/repl_client.py
so that acw_client.py stays focused on session management and I/O.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import re
import sys

# ── ANSI colours ─────────────────────────────────────────────

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


# ── Helpers ──────────────────────────────────────────────────


def format_model(model: str) -> str:
    """Format model name to match CLI style: 'haiku' → 'Haiku 4.5'."""
    model_map = {
        "haiku": "Haiku 4.5",
        "sonnet": "Sonnet 4.5",
        "opus": "Opus 4.5",
    }
    return model_map.get(model.lower(), model) if model else ""


def clean_tool_output(output: str) -> str:
    """
    Clean tool result output — strip raw SDK wrapper dicts and
    agent metadata noise from the output.
    """
    if not output:
        return output

    # Match patterns like {'type': 'text', 'text': '...'} or {"type": "text", "text": "..."}
    cleaned = re.sub(
        r"\{['\"]type['\"]\s*:\s*['\"]text['\"]\s*,\s*['\"]text['\"]\s*:\s*['\"]",
        "",
        output,
    )
    cleaned = re.sub(r"['\"]\s*\}\s*$", "", cleaned)
    cleaned = re.sub(
        r"['\"]\s*\}\s*\{['\"]type['\"]\s*:\s*['\"]text['\"]\s*,\s*['\"]text['\"]\s*:\s*['\"]",
        "\n",
        cleaned,
    )

    # Strip agentId and usage metadata
    cleaned = re.sub(r"['\"]?\}?\s*agentId:.*$", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\\n<usage>.*?</usage>", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.replace("\\n", "\n")

    return cleaned.strip()


# ── Markdown → ANSI rendering ────────────────────────────────


def md_to_ansi(text: str) -> str:
    """
    Convert inline markdown to ANSI terminal formatting.
    Handles: **bold**, `code`, ### headings, --- horizontal rules.
    """
    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.strip()

        # Horizontal rules
        if re.match(r"^[-*_]{3,}\s*$", stripped):
            result.append(f"{DIM}{'─' * 40}{RESET}")
            continue

        # Headings
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_match:
            heading_text = heading_match.group(2)
            heading_text = md_inline(heading_text)
            result.append(f"{BOLD}{heading_text}{RESET}")
            continue

        result.append(md_inline(line))

    return "\n".join(result)


def md_inline(text: str) -> str:
    """Convert inline markdown: **bold**, `code`."""
    text = re.sub(r"\*\*(.+?)\*\*", rf"{BOLD}\1{RESET}", text)
    text = re.sub(r"__(.+?)__", rf"{BOLD}\1{RESET}", text)
    text = re.sub(r"`([^`]+)`", rf"{CYAN}\1{RESET}", text)
    return text


# ── Table-aware text renderer ────────────────────────────────


class TableRenderer:
    """
    Buffers streaming text to detect markdown tables and render them
    with box-drawing characters. Non-table text passes through immediately.
    """

    def __init__(self):
        self._line_buf = ""
        self._table_rows = []
        self._in_table = False
        self._flushed_raw = ""
        self._was_flushed = False

    def feed(self, text: str) -> str:
        """Feed streaming text. Returns rendered output to write."""
        output = ""

        for ch in text:
            if ch == "\n":
                full_line = self._flushed_raw + self._line_buf
                was_flushed = self._was_flushed
                self._line_buf = ""
                self._flushed_raw = ""
                self._was_flushed = False
                output += self._process_line(full_line, was_flushed)
            else:
                self._line_buf += ch

        # Flush partial non-table lines immediately for smooth streaming
        if self._line_buf and not self._in_table:
            s = self._line_buf.lstrip()
            needs_full_line = (
                s.startswith("|")
                or s.startswith("#")
                or (len(s) <= 5 and re.match(r"^[-*_]+$", s))
            )
            if not needs_full_line:
                self._flushed_raw += self._line_buf
                self._was_flushed = True
                output += self._line_buf
                self._line_buf = ""

        return output

    def flush(self) -> str:
        """Flush any remaining buffered content.

        IMPORTANT: Must clear ALL buffers including _flushed_raw.
        Otherwise text from before a tool event leaks into the next
        text block, causing duplication.
        """
        output = ""
        if self._table_rows:
            output += self._render_table()
        if self._line_buf:
            output += md_to_ansi(self._line_buf)
            self._line_buf = ""
        # Clear flushed-raw state so old text doesn't leak into
        # the next text block after a tool event interruption.
        self._flushed_raw = ""
        self._was_flushed = False
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
            if not is_separator:
                self._table_rows.append(stripped)
            return ""
        else:
            output = ""
            if self._in_table:
                output += self._render_table()
                self._in_table = False

            # Detect mid-line headings
            heading_mid = re.search(r"(?<=\S)(#{1,4}\s+\S)", line)
            if heading_mid and heading_mid.start() > 0:
                before = line[: heading_mid.start()]
                after = line[heading_mid.start() :]
                if was_flushed:
                    output += f"\r\033[2K{md_to_ansi(before)}\n"
                else:
                    output += md_to_ansi(before) + "\n"
                output += md_to_ansi(after) + "\n"
                return output

            formatted = md_to_ansi(line)

            if was_flushed:
                if formatted != line:
                    output += f"\r\033[2K{formatted}\n"
                else:
                    output += "\n"
            else:
                output += formatted + "\n"
            return output

    def _render_table(self) -> str:
        if not self._table_rows:
            return ""

        parsed: list[list[str]] = []
        for row in self._table_rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            parsed.append(cells)
        self._table_rows = []

        if not parsed:
            return ""

        num_cols = max(len(row) for row in parsed)
        col_widths = [0] * num_cols
        for row in parsed:
            for i, cell in enumerate(row):
                if i < num_cols:
                    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                    plain = re.sub(r"`([^`]+)`", r"\1", plain)
                    col_widths[i] = max(col_widths[i], len(plain))

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
                plain = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                plain = re.sub(r"`([^`]+)`", r"\1", plain)
                pad = col_widths[i] - len(plain)
                rendered_cell = md_inline(cell)
                parts.append(f" {rendered_cell}{' ' * pad} ")
                parts.append("│")
            return "".join(parts) + "\n"

        output = h_line("┌", "┬", "┐")
        for idx, row in enumerate(parsed):
            output += data_row(row)
            if idx == 0 and len(parsed) > 1:
                output += h_line("├", "┼", "┤")
        output += h_line("└", "┴", "┘")

        return output


def truncate_lines(text: str, max_lines: int = 8) -> str:
    """Truncate multi-line text, showing first N lines + count."""
    lines = text.strip().split("\n")
    if len(lines) <= max_lines:
        return "\n      ".join(lines)
    preview = "\n      ".join(lines[:max_lines])
    return f"{preview}\n      {DIM}... ({len(lines)} lines total){RESET}{GREEN}"


# ── SSE Event Rendering ─────────────────────────────────────


def render_event(data: dict) -> str | None:
    """Render a single SSE event as a formatted terminal line."""
    etype = data.get("type", "unknown")

    if etype == "session_info":
        profile = data.get("profile", "?")
        region = data.get("region", "?")
        return f"{BLUE}ℹ Profile: {BOLD}{profile}{RESET}{BLUE}  Region: {region}{RESET}"

    if etype == "message":
        return None

    if etype == "tool_use":
        tool = data.get("tool", "?")
        inp = data.get("input", {})
        status = data.get("status", "")

        if status == "starting":
            return None

        if tool == "Skill":
            skill_name = inp.get("skill", inp.get("name", "?"))
            return f"{CYAN}⏺ Skill(/{skill_name}){RESET}\n{GREEN}  ⎿  Successfully loaded skill{RESET}"
        elif tool == "Task":
            desc = inp.get("description", "")
            if not desc:
                prompt = inp.get("prompt", "?")
                first_line = prompt.split("\n")[0][:80]
                if first_line.startswith("You are acting as"):
                    desc = first_line.replace("You are acting as ", "").rstrip(".")
                else:
                    desc = first_line
            else:
                desc = desc[:80]
            model = inp.get("model", "")
            model_str = f" {format_model(model)}" if model else ""
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
            return None
        else:
            summary = json.dumps(inp)
            if len(summary) > 60:
                summary = summary[:57] + "..."
            return f"{CYAN}⏺ {tool}({summary}){RESET}"

    if etype == "tool_result":
        output = data.get("output", "")
        error = data.get("error")

        if output and ("launching skill" in output.lower()
                       or "successfully loaded skill" in output.lower()
                       or "skill is loading" in output.lower()):
            return None

        if error:
            cleaned = clean_tool_output(error)
            return f"{RED}  ⎿ Error: {cleaned[:200]}{RESET}"
        if not output.strip():
            return None
        cleaned = clean_tool_output(output)
        truncated = truncate_lines(cleaned)
        return f"{GREEN}  ⎿ {truncated}{RESET}"

    if etype == "sub_agent_spawn":
        model = data.get("model", "?")
        task = data.get("task", "")
        first_line = task.split("\n")[0][:80]
        if first_line.startswith("You are acting as"):
            first_line = first_line.replace("You are acting as ", "").rstrip(".")
        model_display = format_model(model)
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

    # Unknown event type
    return f"{DIM}[{etype}] {json.dumps(data)[:120]}{RESET}"
