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

Type `/retrospect` in the prompt. It automatically finds and analyzes **all** conversation sessions for the current project — no session ID needed.

```
/retrospect
```

Claude will also auto-invoke this skill when you say things like "复盘", "review this session", or "批评与自我批评".

### In other tools

Use the trigger phrases directly in your prompt:

- `复盘` / `retrospect` / `session review` / `批评与自我批评`
- "review this session"
- "how did I do with my prompts?"
- "what mistakes did you make?"

## Installation

### Claude Code (Marketplace)

This repo doubles as a plugin marketplace, so you can install via the official plugin system:

```bash
# Step 1: Add this repo as a marketplace
claude plugin marketplace add zbc0315/retrospect

# Step 2: Install the plugin
claude plugin install retrospect@retrospect-marketplace
```

Or via the interactive prompt:

```
/plugin marketplace add zbc0315/retrospect
/plugin install retrospect@retrospect-marketplace
```

After installation, `/retrospect` appears in the slash command menu.

### Claude Code (Manual)

If you prefer a simpler approach, clone directly to the skills directory:

```bash
# Personal scope (all your projects)
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.claude/skills/retrospect

# Project scope (current project only)
mkdir -p .claude/skills
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect .claude/skills/retrospect
```

### Codex (OpenAI)

```bash
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.codex/skills/retrospect
```

### OpenCode

```bash
# OpenCode also reads from ~/.claude/skills/
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.config/opencode/skills/retrospect
```

### ClawHub (third-party registry)

```bash
clawhub install retrospect
```

> **Note:** [ClawHub](https://clawhub.ai) is a third-party, open-source skill registry — not an official Anthropic product. It works with Claude Code, Codex, OpenCode, and other compatible tools.

## Requirements

- **Node.js** (for the JSONL parser script — uses only built-in modules, no npm install needed)

## How it works

```
/retrospect
    │
    ├─ 1. Auto-discover ALL session JSONL files for the current project
    │     (Claude Code / Codex / OpenCode — no session ID needed)
    │
    ├─ 2. Run parse_session.py → merged Markdown transcript
    │     (older sessions summarized, recent sessions in full detail)
    │
    ├─ 3. Spawn analysis subagent with transcript
    │
    └─ 4. Write FEEDBACK_TO_HUMAN.md + FEEDBACK_TO_LLM.md
```

The skill bundles a Node.js parser (`scripts/parse_session.js`) that converts session JSONL files into readable Markdown transcripts. Supported transcript locations:

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
