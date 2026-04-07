# Retrospect

Session retrospective skill for AI coding assistants. Analyzes conversation history and produces structured feedback for both the user and the LLM.

## What it does

When invoked, this skill:

1. Reads the current (or specified) session's conversation history from the JSONL log
2. Spawns a subagent to perform a structured analysis
3. Writes two files to your project root:

| File | Content |
|------|---------|
| `FEEDBACK_TO_HUMAN.md` | Critique of the user's prompting — round-by-round analysis, responsibility attribution when things go wrong, prompting pattern review, and actionable suggestions |
| `FEEDBACK_TO_LLM.md` | Self-critique of the LLM — mistakes made, root cause analysis, counter-intuitive learnings, and self-improvement notes |

## Usage

### In Claude Code

Type `/retrospect` in the prompt to invoke. You can optionally pass a session ID:

```
/retrospect
/retrospect 3e67bdb8
```

Claude will also auto-invoke this skill when you say things like "复盘", "review this session", or "批评与自我批评".

### In other tools

Use the trigger phrases directly in your prompt:

- `复盘` / `retrospect` / `session review` / `批评与自我批评`
- "review this session"
- "how did I do with my prompts?"
- "what mistakes did you make?"

## Installation

### Claude Code

```bash
# Option 1: ClawHub (third-party skill registry)
clawhub install retrospect

# Option 2: Git clone (personal scope — applies to all your projects)
git clone https://github.com/zbc0315/retrospect.git ~/.claude/skills/retrospect

# Option 3: Git clone (project scope — only this project)
git clone https://github.com/zbc0315/retrospect.git .claude/skills/retrospect
```

After installation, restart Claude Code or start a new session. The skill appears in the `/` slash command menu as `/retrospect`.

### Codex (OpenAI)

```bash
# Option 1: ClawHub
clawhub install retrospect --dir ~/.codex/skills

# Option 2: Git clone
git clone https://github.com/zbc0315/retrospect.git ~/.codex/skills/retrospect
```

### OpenCode

```bash
# Option 1: ClawHub
clawhub install retrospect --dir ~/.config/opencode/skills

# Option 2: Git clone (OpenCode also reads from ~/.claude/skills/)
git clone https://github.com/zbc0315/retrospect.git ~/.config/opencode/skills/retrospect
```

### OpenClaw

```bash
clawhub install retrospect
```

> **Note:** [ClawHub](https://clawhub.ai) is a third-party, open-source skill registry — not an official Anthropic product. It works with Claude Code, Codex, OpenCode, and other compatible tools.

## Requirements

- **Python 3** (for the JSONL parser script — uses only the standard library, no pip install needed)

## How it works

```
/retrospect
    │
    ├─ 1. Find session JSONL file
    │     (auto-detects Claude Code / Codex / OpenCode format)
    │
    ├─ 2. Run parse_session.py → Markdown transcript
    │
    ├─ 3. Spawn analysis subagent with transcript
    │
    └─ 4. Write FEEDBACK_TO_HUMAN.md + FEEDBACK_TO_LLM.md
```

The skill bundles a Python parser (`scripts/parse_session.py`) that converts session JSONL files into readable Markdown transcripts. Supported transcript locations:

| Tool | Path |
|------|------|
| Claude Code | `~/.claude/projects/<path>/<session-id>.jsonl` |
| Codex | `~/.codex/sessions/*.jsonl` |
| OpenCode | `~/.local/share/opencode/sessions/*.jsonl` (Linux) / `~/Library/Application Support/opencode/sessions/*.jsonl` (macOS) |

## Example output

### FEEDBACK_TO_HUMAN.md (excerpt)

```markdown
#### Round-by-Round Analysis

### Turn 2: 检索可用 skill
- **请求**: "请你检索有什么claude code的skill可以用于科研论文撰写"
- **清晰度**: 中等。"检索"一词有歧义——本地查找 vs 网络搜索。
- **责任分析**: 主要是用户侧的歧义。"检索"没有限定范围。
```

### FEEDBACK_TO_LLM.md (excerpt)

```markdown
#### Counter-Intuitive Learnings

### 1. macOS 上 Python 环境管理
- **直觉假设**: 可以直接 `pip install` 安装 Python 包。
- **实际情况**: macOS 的 Python 是 externally-managed-environment，
  不允许直接 pip install。必须先创建 venv。
```

## License

MIT
