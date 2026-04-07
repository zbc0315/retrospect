# Retrospect

> [English](#english) | 中文

AI 编程助手的会话复盘技能。分析对话历史，分别为用户和 LLM 生成结构化反馈。

## 功能

调用后，该技能会：

1. 自动发现当前项目的**全部**对话历史（JSONL 日志）
2. 启动 subagent 进行结构化分析
3. 在项目根目录生成两个文件：

| 文件 | 内容 |
|------|------|
| `FEEDBACK_TO_HUMAN.md` | 对用户 prompt 的批评 —— 逐轮分析、责任归属、prompt 模式评估、改进建议 |
| `FEEDBACK_TO_LLM.md` | LLM 的自我批评 —— 犯过的错误、根因分析、反直觉信息、自我改进笔记 |

## 使用方式

### Claude Code

在 prompt 中输入 `/retrospect`，自动发现并分析当前项目的全部会话记录，无需 session ID。

```
/retrospect
```

也可以直接说 "复盘"、"批评与自我批评"、"review this session"，Claude 会自动触发。

### 其他工具

直接使用触发短语：

- `复盘` / `retrospect` / `session review` / `批评与自我批评`
- "review this session"
- "how did I do with my prompts?"

## 安装

### Claude Code（Marketplace）

本仓库同时是一个 plugin marketplace，可通过官方插件系统安装：

```bash
# 第一步：添加 marketplace
claude plugin marketplace add zbc0315/retrospect

# 第二步：安装插件
claude plugin install retrospect@retrospect-marketplace
```

或在交互式 prompt 中：

```
/plugin marketplace add zbc0315/retrospect
/plugin install retrospect@retrospect-marketplace
```

安装后，`/retrospect` 会出现在斜杠命令菜单中。

### Claude Code（手动安装）

```bash
# 个人作用域（所有项目可用）
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.claude/skills/retrospect

# 项目作用域（仅当前项目）
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
# OpenCode 也可以读取 ~/.claude/skills/
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.config/opencode/skills/retrospect
```

### ClawHub（第三方注册表）

```bash
clawhub install retrospect
```

> **注意：** [ClawHub](https://clawhub.ai) 是第三方开源技能注册表，非 Anthropic 官方产品。支持 Claude Code、Codex、OpenCode 等工具。

## 依赖

- **Node.js**（解析脚本仅使用内置模块，无需 npm install）

## 工作原理

```
/retrospect
    │
    ├─ 1. 自动发现当前项目的全部 session JSONL 文件
    │     （支持 Claude Code / Codex / OpenCode）
    │
    ├─ 2. 运行 parse_session.js → 合并为 Markdown 转录稿
    │     （旧会话自动摘要，最近会话保留完整详情）
    │
    ├─ 3. 启动分析 subagent
    │
    └─ 4. 写入 FEEDBACK_TO_HUMAN.md + FEEDBACK_TO_LLM.md
```

解析脚本 (`scripts/parse_session.js`) 支持的会话文件路径：

| 工具 | 路径 |
|------|------|
| Claude Code | `~/.claude/projects/<path>/<session-id>.jsonl` |
| Codex | `~/.codex/sessions/*.jsonl` |
| OpenCode | `~/.local/share/opencode/sessions/*.jsonl` (Linux) / `~/Library/Application Support/opencode/sessions/*.jsonl` (macOS) |

## 输出示例

### FEEDBACK_TO_HUMAN.md（节选）

```markdown
#### 逐轮分析

### Turn 2: 检索可用 skill
- **请求**: "请你检索有什么claude code的skill可以用于科研论文撰写"
- **清晰度**: 中等。"检索"一词有歧义——本地查找 vs 网络搜索。
- **责任分析**: 主要是用户侧的歧义。"检索"没有限定范围。
```

### FEEDBACK_TO_LLM.md（节选）

```markdown
#### 反直觉信息

### 1. macOS 上 Python 环境管理
- **直觉假设**: 可以直接 `pip install` 安装 Python 包。
- **实际情况**: macOS 的 Python 是 externally-managed-environment，
  不允许直接 pip install。必须先创建 venv。
```

## 许可证

MIT

---

<a id="english"></a>

# Retrospect (English)

> 中文 | [English](#english)

Session retrospective skill for AI coding assistants. Analyzes conversation history and produces structured feedback for both the user and the LLM.

## What it does

When invoked, this skill:

1. Auto-discovers **all** conversation sessions for the current project
2. Spawns a subagent to perform a structured analysis
3. Writes two files to your project root:

| File | Content |
|------|---------|
| `FEEDBACK_TO_HUMAN.md` | Critique of the user's prompting — round-by-round analysis, responsibility attribution, prompting pattern review, and actionable suggestions |
| `FEEDBACK_TO_LLM.md` | Self-critique of the LLM — mistakes made, root cause analysis, counter-intuitive learnings, and self-improvement notes |

## Usage

### In Claude Code

Type `/retrospect` in the prompt. It automatically finds and analyzes all conversation sessions for the current project — no session ID needed.

```
/retrospect
```

Claude will also auto-invoke when you say "retrospect", "session review", "review this session", etc.

### In other tools

Use the trigger phrases directly in your prompt:

- `retrospect` / `session review` / `复盘` / `批评与自我批评`
- "review this session"
- "how did I do with my prompts?"

## Installation

### Claude Code (Marketplace)

This repo doubles as a plugin marketplace:

```bash
# Step 1: Add this repo as a marketplace
claude plugin marketplace add zbc0315/retrospect

# Step 2: Install the plugin
claude plugin install retrospect@retrospect-marketplace
```

Or in the interactive prompt:

```
/plugin marketplace add zbc0315/retrospect
/plugin install retrospect@retrospect-marketplace
```

### Claude Code (Manual)

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
git clone https://github.com/zbc0315/retrospect.git /tmp/retrospect-skill \
  && cp -r /tmp/retrospect-skill/skills/retrospect ~/.config/opencode/skills/retrospect
```

### ClawHub (third-party registry)

```bash
clawhub install retrospect
```

> **Note:** [ClawHub](https://clawhub.ai) is a third-party, open-source skill registry — not an official Anthropic product.

## Requirements

- **Node.js** (parser uses only built-in modules, no npm install needed)

## How it works

```
/retrospect
    │
    ├─ 1. Auto-discover ALL session JSONL files for the current project
    │     (Claude Code / Codex / OpenCode)
    │
    ├─ 2. Run parse_session.js → merged Markdown transcript
    │     (older sessions summarized, recent sessions in full detail)
    │
    ├─ 3. Spawn analysis subagent with transcript
    │
    └─ 4. Write FEEDBACK_TO_HUMAN.md + FEEDBACK_TO_LLM.md
```

Supported transcript locations:

| Tool | Path |
|------|------|
| Claude Code | `~/.claude/projects/<path>/<session-id>.jsonl` |
| Codex | `~/.codex/sessions/*.jsonl` |
| OpenCode | `~/.local/share/opencode/sessions/*.jsonl` (Linux) / `~/Library/Application Support/opencode/sessions/*.jsonl` (macOS) |

## License

MIT
