#!/usr/bin/env python3
"""
ACW CLI — Detachable CLI client for AWS Coworker.

A terminal client that connects to a running ACW Server over HTTP/SSE,
replicating the Claude Code CLI experience. The engine runs remotely;
the rendering happens locally.

Usage:
    # Connect to local server (default http://localhost:8080)
    python -m cli.acw_client

    # Connect to remote server with auth
    python -m cli.acw_client --url https://ec2-host:8080 --api-key <secret>

    # Resume an existing session
    python -m cli.acw_client --resume

    # Resume a specific session
    python -m cli.acw_client --session <session-id>

Normally invoked via:
    acw connect [url] [--api-key KEY] [--resume] [--session ID]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .rendering import (
    BOLD, CYAN, DIM, GREEN, RED, RESET, YELLOW,
    Spinner, TableRenderer, render_event,
)
from .transport import HTTPTransport, SessionInfo, Transport


# ── Banner ───────────────────────────────────────────────────


def _print_banner(url: str):
    """Print the ACW CLI connection banner."""
    print(f"{BOLD}AWS Coworker — Remote CLI{RESET}")
    print(f"{DIM}Server: {url}{RESET}")
    print(f"{DIM}Type 'exit' or Ctrl+C to quit. '/sessions' to list sessions.{RESET}")
    print()


# ── Session picker ───────────────────────────────────────────


async def _pick_session(transport: Transport, profile: str, region: str) -> SessionInfo | None:
    """Interactive session picker for --resume mode."""
    sessions = await transport.list_sessions()
    active = [s for s in sessions if s.status in ("active", "idle")]

    if not active:
        print(f"{DIM}No existing sessions found. Creating a new one.{RESET}")
        return await transport.create_session(profile, region)

    print(f"{BOLD}Existing sessions:{RESET}")
    for i, s in enumerate(active, 1):
        prof = s.profile or "(default)"
        reg = s.region or "(default)"
        created = f"  created: {s.created_at}" if s.created_at else ""
        print(f"  {CYAN}{i}.{RESET} {s.id[:12]}  {DIM}profile={prof}  region={reg}{created}{RESET}")
    print(f"  {CYAN}n.{RESET} {DIM}Create new session{RESET}")
    print()

    while True:
        try:
            choice = input(f"{BOLD}Select session [{len(active) + 1} choices]: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if choice.lower() in ("n", "new", ""):
            return await transport.create_session(profile, region)

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(active):
                return active[idx]
        except ValueError:
            pass

        print(f"{RED}Invalid choice. Enter 1-{len(active)} or 'n' for new.{RESET}")


# ── Stream message ───────────────────────────────────────────


async def stream_message(transport: Transport, session_id: str, content: str):
    """Send a message and stream SSE events to the terminal."""

    in_text = False
    pending_ws = ""
    table = TableRenderer()
    spinner = Spinner("Thinking")
    spinner.start()

    try:
        async for data in transport.send_message(session_id, content):
            etype = data.get("type", "")

            # Handle streaming text deltas inline
            if etype == "message":
                delta = data.get("delta", True)
                text = data.get("content", "")
                if delta and text:
                    if not in_text and text.strip() == "":
                        pending_ws += text
                    else:
                        await spinner.stop()
                        if not in_text:
                            pending_ws = pending_ws.lstrip("\n")
                            if pending_ws:
                                sys.stdout.write(pending_ws)
                            pending_ws = ""
                        in_text = True
                        rendered_text = table.feed(text)
                        if rendered_text:
                            sys.stdout.write(rendered_text)
                            sys.stdout.flush()
                continue

            # For non-message events, check if it renders to anything
            rendered = render_event(data)

            if rendered:
                if in_text:
                    remaining = table.flush()
                    if remaining:
                        sys.stdout.write(remaining)
                    print()
                    in_text = False
                pending_ws = ""
                await spinner.stop()
                print(rendered)
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

    except ConnectionError as e:
        await spinner.stop()
        print(f"{RED}{e}{RESET}")
        return

    # Clean up
    remaining = table.flush()
    if remaining:
        sys.stdout.write(remaining)
    await spinner.stop()
    if in_text:
        print()


# ── REPL commands ────────────────────────────────────────────


async def _handle_repl_command(cmd: str, transport: Transport, session: SessionInfo) -> SessionInfo | None:
    """Handle REPL meta-commands (prefixed with /). Returns new session if switched, else None."""
    if cmd in ("/sessions", "/list"):
        sessions = await transport.list_sessions()
        if not sessions:
            print(f"{DIM}No sessions found.{RESET}")
        else:
            print(f"{BOLD}Sessions:{RESET}")
            for s in sessions:
                marker = f" {GREEN}← current{RESET}" if s.id == session.id else ""
                prof = s.profile or "(default)"
                print(f"  {s.id[:12]}  {DIM}profile={prof}  status={s.status}{RESET}{marker}")
        print()
        return None

    if cmd.startswith("/switch "):
        target = cmd.split(" ", 1)[1].strip()
        sessions = await transport.list_sessions()
        match = [s for s in sessions if s.id.startswith(target)]
        if len(match) == 1:
            print(f"{GREEN}Switched to session {match[0].id[:12]}{RESET}")
            return match[0]
        elif len(match) > 1:
            print(f"{YELLOW}Ambiguous — multiple sessions match '{target}'.{RESET}")
        else:
            print(f"{RED}No session matching '{target}'.{RESET}")
        return None

    if cmd in ("/new",):
        new_session = await transport.create_session(session.profile, session.region)
        print(f"{GREEN}Created new session: {new_session.id[:12]}{RESET}")
        return new_session

    if cmd in ("/help", "/?"):
        print(f"{BOLD}REPL commands:{RESET}")
        print(f"  {CYAN}/sessions{RESET}  — List all sessions")
        print(f"  {CYAN}/switch <id>{RESET} — Switch to a different session")
        print(f"  {CYAN}/new{RESET}       — Create a new session")
        print(f"  {CYAN}/help{RESET}      — Show this help")
        print(f"  {CYAN}exit{RESET}       — Quit the CLI")
        print()
        return None

    print(f"{YELLOW}Unknown command: {cmd}. Type /help for available commands.{RESET}")
    return None


# ── Main ─────────────────────────────────────────────────────


async def run(
    url: str = "http://localhost:8080",
    api_key: str | None = None,
    profile: str = "",
    region: str = "",
    session_id: str | None = None,
    resume: bool = False,
):
    """Main entry point for the ACW CLI client."""
    transport = HTTPTransport(base_url=url, api_key=api_key)

    try:
        # Health check
        if not await transport.health_check():
            print(f"{RED}Cannot connect to {url} — is the server running?{RESET}")
            print(f"{DIM}Start the server with: acw server{RESET}")
            return 1

        _print_banner(url)
        print(f"{GREEN}Connected to server{RESET}")

        # Session setup
        if session_id:
            # Direct session ID provided
            session = SessionInfo(id=session_id, profile=profile, region=region)
            print(f"{DIM}Resuming session: {session_id[:12]}{RESET}")
        elif resume:
            # Interactive session picker
            session = await _pick_session(transport, profile, region)
            if session is None:
                return 0
        else:
            # New session
            session = await transport.create_session(profile, region)
            profile_display = session.profile or "(default)"
            region_display = session.region or "(default)"
            print(f"{DIM}Session: {session.id[:12]}  Profile: {profile_display}  Region: {region_display}{RESET}")

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

            # REPL meta-commands
            if user_input.startswith("/"):
                new_session = await _handle_repl_command(user_input, transport, session)
                if new_session:
                    session = new_session
                continue

            print()
            await stream_message(transport, session.id, user_input)
            print()

    finally:
        await transport.close()

    return 0


def main():
    """CLI entry point — parses args and runs the async client."""
    parser = argparse.ArgumentParser(
        description="ACW CLI — Connect to a running AWS Coworker server",
        prog="acw connect",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=os.getenv("ACW_SERVER_URL", "http://localhost:8080"),
        help="Server URL (default: $ACW_SERVER_URL or http://localhost:8080)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ACW_API_KEY"),
        help="API key for remote server auth (default: $ACW_API_KEY)",
    )
    parser.add_argument("--profile", default="", help="AWS profile name")
    parser.add_argument("--region", default="", help="AWS region")
    parser.add_argument("--session", default=None, help="Resume a specific session by ID")
    parser.add_argument("--resume", action="store_true", help="List and resume an existing session")
    args = parser.parse_args()

    exit_code = asyncio.run(run(
        url=args.url,
        api_key=args.api_key,
        profile=args.profile,
        region=args.region,
        session_id=args.session,
        resume=args.resume,
    ))
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
