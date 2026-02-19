# Research: Claude Agent SDK vs Claude Code Subprocess

**Status:** Complete
**Created:** 2026-02-18
**Context:** Open Question #2 from PLAN-WEB-UI-AND-DEPLOYMENT.md — the team asked for research into the differences between the Claude Agent SDK and Claude Code subprocess before deciding which to use for the FastAPI web wrapper.

---

## Executive Summary

**Recommendation: Use the Claude Agent SDK with `ClaudeSDKClient` for the web wrapper.**

The SDK is the clear winner for our use case. It's the same codebase as Claude Code (the SDK is what Claude Code is built on), it's what the AWS sample project uses for AgentCore, and it solves the critical performance problem — subprocess spawns a new process per request (~12 seconds each), while `ClaudeSDKClient` pays that cost once per session and reuses the process for subsequent messages.

The team's concern about skills, commands, and sub-agents was valid but the answer is reassuring: these are files on disk. The SDK session has the same filesystem access as the CLI. When Claude reads a skill file via the Read tool, it doesn't matter whether the session was started by the CLI or the SDK — the file is the same.

---

## What Is the Claude Agent SDK?

The Claude Agent SDK is the Python/TypeScript library that Claude Code itself is built on. It's not a separate product — it's the engine extracted as a library. Published on PyPI as `claude-agent-sdk`, documented at platform.claude.com.

The SDK exposes two APIs:

1. **`query()` — stateless, one-shot.** Creates a new process per call. Good for batch scripts. Each call costs ~12 seconds startup.

2. **`ClaudeSDKClient` — stateful, multi-turn.** Spawns a single long-lived Claude Code process and communicates via stdin/stdout binary protocol. First call costs ~12 seconds; subsequent calls reuse the process (~0.1 seconds). This is the right choice for a web service.

---

## Comparison

### Feature Matrix

| Capability | Claude Agent SDK | Subprocess (`claude -p`) |
|---|---|---|
| Core tools (Read, Write, Bash, Glob, Grep, Edit) | Yes | Yes |
| Task tool (sub-agents) | Yes | Yes |
| TodoWrite | Yes | Yes |
| Custom MCP tools (in-process) | Yes | No |
| Permission callbacks (`can_use_tool`) | Yes | No |
| Hooks (PreToolUse, PostToolUse) | Yes | No |
| CLAUDE.md loading | Yes (via `setting_sources`) | Partial (`--system-prompt` flag) |
| Skills/commands/agents (files on disk) | Yes — same filesystem access | Yes — same filesystem access |
| Streaming | Native async/await | Manual JSON line parsing |
| Session continuity | Built-in (`ClaudeSDKClient`) | Manual (`--resume SESSION_ID`) |
| Error handling | Typed Python exceptions | Exit codes + stderr parsing |
| Type safety | Full Python type hints | None |

### Performance

| Approach | First Request | Subsequent Requests |
|---|---|---|
| SDK `query()` (stateless) | ~12s | ~12s each (new process) |
| SDK `ClaudeSDKClient` (stateful) | ~12s | ~0.1s each (reuse process) |
| Subprocess `claude -p` | ~12s | ~12s each (new process) |
| Subprocess `claude -p --resume` | ~12s | ~12s each (new process, resumes context) |

For an interactive web UI where a user sends multiple messages in a conversation, the SDK's `ClaudeSDKClient` is the only approach that doesn't impose a 12-second penalty per message.

### What the Subprocess Approach Looks Like

```bash
# Basic non-interactive call
claude -p "Your prompt" --output-format json

# Streaming
claude -p "Your prompt" --output-format stream-json --include-partial-messages

# Resume session
claude -p "Follow-up" --resume SESSION_ID --output-format json
```

Known issues with subprocess mode: TTY handling can cause hangs, large stdin inputs have buffer overflow issues, and tool permissions may be re-requested even when configured.

### What the SDK Approach Looks Like

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code"},
    setting_sources=["project"],  # Loads CLAUDE.md from working directory
    allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "TodoWrite"],
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("List my S3 buckets")
    async for msg in client.receive_response():
        yield msg  # Stream to SSE endpoint
```

---

## The AWS Sample Project

The official AWS sample (`aws-samples/sample-claude-code-web-agent-on-bedrock-agentcore`) uses the **Claude Agent SDK**, not subprocess. Their architecture:

- FastAPI backend with `ClaudeSDKClient` for sessions
- SessionManager mapping session IDs to SDK client instances
- Permission control via `can_use_tool` callback
- `ALLOWED_TOOLS` configuration for tool whitelisting
- S3 workspace sync for persistence
- SSE streaming for real-time responses
- `/invocations` + `/ping` on port 8080 (AgentCore protocol)

They chose the SDK because:
1. Multi-turn conversations need session state across HTTP requests
2. 12-second latency per message is unacceptable for a web UI
3. Permission callbacks give fine-grained control over tool execution
4. Clean integration with the AgentCore invocation model

---

## The Team's Concern: Skills, Commands, and Sub-Agents

The meeting raised a valid question: does the SDK support skills, commands, and sub-agents the way the CLI does?

**Answer: Yes, because these are files on disk, not CLI features.**

Here's what happens when Claude Code loads a skill:
1. Claude's system prompt (CLAUDE.md) tells it skills exist in `skills/`
2. Claude uses the Read tool to read the skill's SKILL.md file
3. Claude follows the instructions in that file

Step 2 works identically whether the session was started by the CLI or the SDK. The Read tool reads a file. It doesn't know or care how the session was started.

The same applies to:
- **Slash commands** (`.claude/commands/*.md`) — these are prompt templates. The SDK session reads them via the Read tool.
- **Agent definitions** (`.claude/agents/*.md`) — these are markdown files describing sub-agent roles. The Task tool spawns sub-agents the same way regardless of how the parent session started.
- **CLAUDE.md** — loaded via `setting_sources=["project"]` in the SDK, or by being in the working directory.

**One nuance:** The SDK also supports defining agents programmatically via `AgentDefinition` objects in Python. This is an additional option, not a replacement. You can use both: files on disk for the existing agent definitions, and programmatic definitions for any new web-specific agents.

---

## Recommendation

**Use the Claude Agent SDK with `ClaudeSDKClient` for the FastAPI web wrapper.**

Rationale:

1. **Performance**: `ClaudeSDKClient` reuses the Claude process across messages in a session. For a chat interface, this means ~12 seconds for the first message and near-instant startup for subsequent messages. Subprocess would impose ~12 seconds per message — unusable for an interactive web UI.

2. **Session management**: The SDK handles session state natively. No need to track session IDs and pass `--resume` flags.

3. **Permission control**: The `can_use_tool` callback lets us implement the approval UI — when Claude wants to run a mutation, we can pause the session, send a permission request to the frontend, and resume when the user approves.

4. **AgentCore compatibility**: The AWS sample proves this architecture works on AgentCore. Same container, same code.

5. **Skills/commands/agents work unchanged**: Files on disk. No migration needed.

6. **Streaming**: Native async/await maps cleanly to SSE endpoints in FastAPI.

### What We Don't Need to Change

- Skills (markdown files) — work as-is
- Commands (markdown files) — work as-is
- Agent definitions (markdown files) — work as-is
- CLAUDE.md — loaded via `setting_sources`
- Sub-agent model hierarchy (Opus/Sonnet/Haiku) — configured in SDK options

### What We Do Need to Build

- FastAPI server with session management
- SSE streaming endpoint
- Permission approval flow (frontend ↔ backend)
- Container packaging (ARM64, port 8080)
- `/invocations` + `/ping` endpoints (AgentCore protocol)

### Migration Path

No migration needed. The SDK wraps the same Claude Code process. Our existing files on disk (skills, commands, agents, CLAUDE.md) are consumed the same way. We're adding a web layer on top, not replacing the CLI.

The CLI (`./acw`) continues to work unchanged for local use. The web wrapper (`./acw --server`) starts a FastAPI server that uses the SDK instead.

---

## Open Item

One thing to verify during Phase 2 implementation: confirm that `setting_sources=["project"]` correctly loads CLAUDE.md from the container's working directory when running inside Docker. If not, we can fall back to passing the CLAUDE.md content directly as the `system_prompt` parameter.

---

## Sources

- Claude Agent SDK Python docs: platform.claude.com/docs/en/agent-sdk/python
- Claude Agent SDK overview: platform.claude.com/docs/en/agent-sdk/overview
- Claude Code headless mode: code.claude.com/docs/en/headless
- AWS sample project: github.com/aws-samples/sample-claude-code-web-agent-on-bedrock-agentcore
- Bedrock AgentCore runtime requirements: docs.aws.amazon.com/bedrock-agentcore
