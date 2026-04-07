#!/usr/bin/env python3
"""Parse AI coding assistant session JSONL files into readable Markdown transcripts.

Supports: Claude Code, Codex (OpenAI), OpenCode, and generic JSONL chat formats.

Usage:
    python3 parse_session.py <path-to-session.jsonl>

Outputs Markdown to stdout. Redirect to a file as needed.
"""

import json
import sys
from pathlib import Path


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


def build_markdown(exchanges):
    """Convert exchange list to Markdown transcript."""
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

    return "\n".join(output)


def parse_session(jsonl_path: str) -> str:
    """Parse JSONL file and return Markdown transcript. Auto-detects format."""
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
        exchanges = parse_claude_code(lines)
    elif fmt == "openai":
        exchanges = parse_openai_format(lines)
    else:
        cc = parse_claude_code(lines)
        oai = parse_openai_format(lines)
        exchanges = cc if len(cc) >= len(oai) else oai

    return build_markdown(exchanges)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <session.jsonl>", file=sys.stderr)
        sys.exit(1)

    jsonl_path = sys.argv[1]
    if not Path(jsonl_path).exists():
        print(f"Error: {jsonl_path} not found", file=sys.stderr)
        sys.exit(1)

    print(parse_session(jsonl_path))
