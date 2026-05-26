# MarkItDown Auto Converter Agent Skill / MarkItDown 自动转换 Agent Skill

[English](#english) | [中文](#中文)

---

## English

A portable document-to-Markdown conversion skill for Hermes Agent, Claude Code, Codex/OpenAI agents, Cursor, and generic agent frameworks. It uses [Microsoft MarkItDown](https://github.com/microsoft/markitdown) where appropriate and avoids unsafe full-table conversion for large CSV/Excel files.

### What this skill does

- Converts small PDFs, Word files, PowerPoint files, HTML, EPUB, text files, and images to Markdown.
- Produces previews for medium/large documents to avoid context overflow.
- Summarizes large CSV/Excel files with pandas instead of generating massive Markdown tables.
- Provides a standalone script: `scripts/convert_and_verify.py`.
- Ships with compatibility files for Hermes, Claude Code, Codex/OpenAI agents, and Cursor.

### Repository structure

```text
markitdown-auto-converter-agent-skill/
├── SKILL.md                                        # Canonical cross-agent skill
├── README.md
├── LICENSE
├── agent instruction file                                      # Codex / OpenAI agent instructions
├── Claude-compatible instruction file                                      # Claude Code instructions
├── Cursor rule adapter                                   # Legacy Cursor rules
├── IDE rule adapter directory/markitdown-auto-converter.mdc    # Cursor rule file
├── scripts/
│   └── convert_and_verify.py                      # Standalone conversion router
└── skills/
    └── productivity/
        └── markitdown-auto-converter-agent-skill/
            ├── SKILL.md                           # Hermes-compatible copy
            └── scripts/
                └── convert_and_verify.py
```

### Installation

#### Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

#### Hermes Agent

```bash
git clone https://github.com/yanyintingyou/markitdown-auto-converter-agent-skill.git
mkdir -p ~/.hermes/skills/productivity
cp -r markitdown-auto-converter-agent-skill/skills/productivity/markitdown-auto-converter-agent-skill ~/.hermes/skills/productivity/
```

Restart Hermes or start a new session.

#### Claude Code

Clone the repository into your project or skill collection. Claude Code reads a repository-level compatibility adapter that points to `SKILL.md`.

#### Codex / OpenAI agents

Keep the repository-level compatibility adapter at repository root. Codex-style agents should load `SKILL.md` and may call `scripts/convert_and_verify.py`.

#### Cursor

Open the repository or copy `IDE rule adapter directory/markitdown-auto-converter.mdc` into your project’s `IDE rule adapter directory` directory.

### Usage

```bash
python3 scripts/convert_and_verify.py --file report.pdf --output /tmp/report.md
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/data_summary.md
```

Agent prompt examples:

```text
Convert this annual report PDF to Markdown.
```

```text
把这个 Excel 转成 Markdown；如果太大就先给我 pandas 摘要。
```

### Design rule

CSV/Excel files larger than 2 MB are **not** converted into full Markdown tables. They are summarized with pandas to avoid context overflow.

---

## 中文

这是一个可移植的文档转 Markdown Agent Skill，兼容 Hermes Agent、Claude Code、Codex/OpenAI Agents、Cursor 与通用 Agent 框架。它在合适场景下调用 [Microsoft MarkItDown](https://github.com/microsoft/markitdown)，并避免把大型 CSV/Excel 强行转换成巨大的 Markdown 表格。

### 功能概览

- 将小型 PDF、Word、PPT、HTML、EPUB、文本文件和图片转换为 Markdown。
- 对中大型文档生成预览，避免撑爆上下文窗口。
- 对大型 CSV/Excel 使用 pandas 生成数据探索摘要，而不是输出超大 Markdown 表格。
- 提供独立脚本：`scripts/convert_and_verify.py`。
- 提供 Hermes、Claude Code、Codex/OpenAI Agents、Cursor 兼容文件。

### 仓库结构

```text
markitdown-auto-converter-agent-skill/
├── SKILL.md                                        # 跨 Agent 通用主技能文件
├── README.md
├── LICENSE
├── agent instruction file                                      # Codex / OpenAI Agent 指令
├── Claude-compatible instruction file                                      # Claude Code 指令
├── Cursor rule adapter                                   # Cursor 旧版规则
├── IDE rule adapter directory/markitdown-auto-converter.mdc    # Cursor 新版规则
├── scripts/
│   └── convert_and_verify.py                      # 独立转换与路由脚本
└── skills/
    └── productivity/
        └── markitdown-auto-converter-agent-skill/
            ├── SKILL.md                           # Hermes 标准安装路径
            └── scripts/
                └── convert_and_verify.py
```

### 安装方式

#### Python 依赖

```bash
python3 -m pip install -r requirements.txt
```

#### Hermes Agent

```bash
git clone https://github.com/yanyintingyou/markitdown-auto-converter-agent-skill.git
mkdir -p ~/.hermes/skills/productivity
cp -r markitdown-auto-converter-agent-skill/skills/productivity/markitdown-auto-converter-agent-skill ~/.hermes/skills/productivity/
```

然后重启 Hermes 或开启新会话。

#### Claude Code

把本仓库克隆到项目目录或技能集合中。Claude Code 可读取仓库级兼容性适配文件，并由该文件指向 `SKILL.md`。

#### Codex / OpenAI Agents

保留根目录的兼容性适配文件。Codex 风格 Agent 应加载 `SKILL.md`，并可调用 `scripts/convert_and_verify.py`。

#### Cursor

直接打开本仓库，或将 `IDE rule adapter directory/markitdown-auto-converter.mdc` 复制到项目的 `IDE rule adapter directory` 目录。

### 使用方式

```bash
python3 scripts/convert_and_verify.py --file report.pdf --output /tmp/report.md
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/data_summary.md
```

Agent 提示示例：

```text
把这份年报 PDF 转成 Markdown。
```

```text
把这个 Excel 转成 Markdown；如果太大就先给我 pandas 摘要。
```

### 设计原则

超过 2 MB 的 CSV/Excel **不做完整 Markdown 表格转换**，而是生成 pandas 数据探索摘要，避免上下文溢出和无意义的大表输出。
