#!/usr/bin/env python3
"""Parse AI coding assistant session JSONL files into readable Markdown transcripts.

Supports: Claude Code, Codex (OpenAI), OpenCode, and generic JSONL chat formats.

Usage:
    # Parse all sessions for a project (auto-discovers JSONL files):
    python3 parse_session.py --project-dir /path/to/project

    # Parse a single JSONL file:
    python3 parse_session.py /path/to/session.jsonl

Outputs Markdown to stdout. Redirect to a file as needed.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Older sessions beyond this count are summarized (user messages only)
# to keep the transcript manageable. Most recent sessions get full detail.
FULL_DETAIL_SESSIONS = 5
MAX_SUMMARY_TURNS = 10


def extract_text_from_content(content):
    """Extract readable text from message content (string or content blocks)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "text":
                parts.append(block["text"].strip())
            elif btype == "tool_use":
                name = block.get("name", "unknown")
                inp = block.get("input", {})
                if name in ("Read", "Glob", "Grep", "read_file", "grep", "glob"):
                    target = inp.get("file_path") or inp.get("pattern") or inp.get("path", "")
                    parts.append(f"[Tool: {name}({target})]")
                elif name in ("Bash", "shell", "run_command"):
                    cmd = inp.get("command", "")
                    if len(cmd) > 200:
                        cmd = cmd[:200] + "..."
                    parts.append(f"[Tool: {name}] {cmd}")
                elif name in ("Write", "Edit", "write_file", "edit_file"):
                    fp = inp.get("file_path", "")
                    parts.append(f"[Tool: {name}({fp})]")
                elif name in ("Agent", "spawn_agent"):
                    desc = inp.get("description", inp.get("prompt", ""))[:100]
                    parts.append(f"[Tool: Agent({desc})]")
                else:
                    parts.append(f"[Tool: {name}]")
            elif btype == "tool_result":
                result_content = block.get("content", "")
                if isinstance(result_content, str) and result_content.strip():
                    text = result_content.strip()
                    if len(text) > 300:
                        text = text[:300] + "... [truncated]"
                    parts.append(f"[Tool Result] {text}")
                elif isinstance(result_content, list):
                    for sub in result_content:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            text = sub["text"].strip()
                            if len(text) > 300:
                                text = text[:300] + "... [truncated]"
                            parts.append(f"[Tool Result] {text}")
            elif btype == "function_call":
                fname = block.get("name", "unknown")
                parts.append(f"[Function: {fname}]")
            elif btype == "thinking":
                pass
        return "\n".join(parts)
    return ""


def detect_format(obj):
    """Detect JSONL format from a sample object."""
    if "type" in obj and obj["type"] in ("user", "assistant", "system", "file-history-snapshot"):
        return "claude-code"
    if "role" in obj and "content" in obj:
        return "openai"
    return "unknown"


def parse_claude_code(lines):
    """Parse Claude Code JSONL format."""
    exchanges = []
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type", "")

        if msg_type in ("file-history-snapshot", "attachment"):
            continue
        if obj.get("isMeta"):
            continue

        if msg_type == "user":
            content = obj.get("message", {}).get("content", "")
            text = extract_text_from_content(content)
            if text and "<command-name>" in text:
                continue
            if text and not text.startswith("[Tool Result]"):
                exchanges.append(("user", text))
            elif text:
                exchanges.append(("tool_result", text))

        elif msg_type == "assistant":
            content = obj.get("message", {}).get("content", [])
            text = extract_text_from_content(content)
            if text:
                exchanges.append(("assistant", text))

        elif msg_type == "system":
            content = obj.get("content", "")
            if content and len(content.strip()) > 10:
                subtype = obj.get("subtype", "")
                if subtype != "local_command":
                    exchanges.append(("system", content.strip()[:500]))

    return exchanges


def parse_openai_format(lines):
    """Parse OpenAI/Codex/OpenCode JSONL format (role/content pairs)."""
    exchanges = []
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = obj.get("role", "")
        content = obj.get("content", "")
        text = extract_text_from_content(content)

        if not text:
            continue

        if role in ("user", "human"):
            exchanges.append(("user", text))
        elif role in ("assistant", "model"):
            exchanges.append(("assistant", text))
        elif role == "system":
            if len(text) > 10:
                exchanges.append(("system", text[:500]))
        elif role == "tool":
            if len(text) > 10:
                exchanges.append(("tool_result", text[:300]))

    return exchanges


def parse_single_file(jsonl_path):
    """Parse a single JSONL file. Auto-detects format."""
    lines = Path(jsonl_path).read_text().strip().split("\n")

    fmt = "unknown"
    for line in lines:
        try:
            obj = json.loads(line)
            fmt = detect_format(obj)
            if fmt != "unknown":
                break
        except json.JSONDecodeError:
            continue

    if fmt == "claude-code":
        return parse_claude_code(lines)
    elif fmt == "openai":
        return parse_openai_format(lines)
    else:
        cc = parse_claude_code(lines)
        oai = parse_openai_format(lines)
        return cc if len(cc) >= len(oai) else oai


def summarize_exchanges(exchanges):
    """Summarize older sessions: keep only user messages, limit count."""
    summary = []
    count = 0
    for role, text in exchanges:
        if role == "user":
            count += 1
            if count > MAX_SUMMARY_TURNS:
                summary.append(("user", f"... [{count}+ more user turns omitted] ..."))
                break
            # Truncate long user messages in summary
            if len(text) > 300:
                text = text[:300] + "... [truncated]"
            summary.append(("user", text))
    return summary


def build_markdown_multi(session_list):
    """Build Markdown from multiple sessions.

    session_list: list of (session_file, mtime, exchanges) sorted oldest-first.
    Older sessions beyond FULL_DETAIL_SESSIONS are summarized.
    """
    output = ["# Project Session Transcripts\n"]
    total = len(session_list)
    full_start = max(0, total - FULL_DETAIL_SESSIONS)

    for i, (session_file, mtime, exchanges) in enumerate(session_list):
        if not exchanges:
            continue

        session_num = i + 1
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        session_id = Path(session_file).stem[:8]

        output.append(f"---\n")
        output.append(f"## Session {session_num} ({date_str}, id: {session_id}...)\n")

        if i < full_start:
            # Summarize older sessions
            output.append(f"*[Summary — {len([e for e in exchanges if e[0] == 'user'])} user turns]*\n")
            summarized = summarize_exchanges(exchanges)
            for role, text in summarized:
                if role == "user":
                    output.append(f"- **User**: {text[:200]}")
            output.append("")
        else:
            # Full detail for recent sessions
            turn_num = 0
            for role, text in exchanges:
                if role == "user":
                    turn_num += 1
                    output.append(f"### Turn {turn_num} — User\n")
                    output.append(text)
                    output.append("")
                elif role == "assistant":
                    output.append(f"#### Assistant Response\n")
                    output.append(text)
                    output.append("")
                elif role == "tool_result":
                    output.append(f"> {text[:200]}")
                    output.append("")
                elif role == "system":
                    output.append(f"*[System: {text[:200]}]*")
                    output.append("")

    return "\n".join(output)


def find_project_sessions(project_dir):
    """Find all session JSONL files for a project directory.

    Searches Claude Code, Codex, and OpenCode session directories.
    Returns list of (filepath, mtime) sorted by mtime (oldest first).
    """
    project_dir = os.path.realpath(project_dir)
    sessions = []

    # Claude Code: ~/.claude/projects/<encoded-path>/*.jsonl
    claude_home = Path.home() / ".claude" / "projects"
    if claude_home.exists():
        # Encode path: /Users/tom/myproject → -Users-tom-myproject
        encoded = "-" + project_dir.lstrip("/").replace("/", "-")
        project_path = claude_home / encoded
        if project_path.exists():
            for f in project_path.glob("*.jsonl"):
                # Skip subagent logs (they're in subdirectories)
                if f.parent == project_path:
                    sessions.append((str(f), f.stat().st_mtime))

    # Codex: ~/.codex/sessions/*.jsonl
    codex_path = Path.home() / ".codex" / "sessions"
    if codex_path.exists():
        for f in codex_path.glob("*.jsonl"):
            sessions.append((str(f), f.stat().st_mtime))

    # OpenCode: platform-dependent
    if sys.platform == "darwin":
        oc_path = Path.home() / "Library" / "Application Support" / "opencode" / "sessions"
    else:
        oc_path = Path.home() / ".local" / "share" / "opencode" / "sessions"
    if oc_path.exists():
        for f in oc_path.glob("*.jsonl"):
            sessions.append((str(f), f.stat().st_mtime))

    # Sort by modification time, oldest first
    sessions.sort(key=lambda x: x[1])
    return sessions


def main():
    if len(sys.argv) < 2:
        print(f"Usage:", file=sys.stderr)
        print(f"  {sys.argv[0]} --project-dir /path/to/project", file=sys.stderr)
        print(f"  {sys.argv[0]} /path/to/session.jsonl", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--project-dir":
        if len(sys.argv) < 3:
            print("Error: --project-dir requires a path argument", file=sys.stderr)
            sys.exit(1)
        project_dir = sys.argv[2]
        if not Path(project_dir).is_dir():
            print(f"Error: {project_dir} is not a directory", file=sys.stderr)
            sys.exit(1)

        sessions = find_project_sessions(project_dir)
        if not sessions:
            print(f"Error: No session files found for project {project_dir}", file=sys.stderr)
            print(f"Searched in ~/.claude/projects/, ~/.codex/sessions/, and opencode sessions", file=sys.stderr)
            sys.exit(1)

        print(f"Found {len(sessions)} session(s)", file=sys.stderr)

        # Parse all sessions
        session_data = []
        for filepath, mtime in sessions:
            exchanges = parse_single_file(filepath)
            if exchanges:  # Skip empty sessions
                session_data.append((filepath, mtime, exchanges))

        if not session_data:
            print("Error: All session files were empty or unparseable", file=sys.stderr)
            sys.exit(1)

        print(f"Parsed {len(session_data)} non-empty session(s)", file=sys.stderr)
        print(build_markdown_multi(session_data))

    else:
        # Single file mode
        jsonl_path = sys.argv[1]
        if not Path(jsonl_path).exists():
            print(f"Error: {jsonl_path} not found", file=sys.stderr)
            sys.exit(1)

        exchanges = parse_single_file(jsonl_path)
        output = ["# Session Transcript\n"]
        turn_num = 0
        for role, text in exchanges:
            if role == "user":
                turn_num += 1
                output.append(f"## Turn {turn_num} — User\n")
                output.append(text)
                output.append("")
            elif role == "assistant":
                output.append(f"### Assistant Response\n")
                output.append(text)
                output.append("")
            elif role == "tool_result":
                output.append(f"> {text[:200]}")
                output.append("")
            elif role == "system":
                output.append(f"*[System: {text[:200]}]*")
                output.append("")
        print("\n".join(output))


if __name__ == "__main__":
    main()
