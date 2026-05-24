---
name: markitdown-auto-converter-agent-skill
description: Use when the user explicitly asks to convert local or remote documents into Markdown. Detects file type and size, routes small documents through Microsoft MarkItDown, summarizes large CSV/Excel files instead of dumping huge Markdown tables, and gives safe fallbacks for oversized or scanned files.
version: 1.1.0
author: yanyintingyou
license: MIT
metadata:
  hermes:
    category: productivity
    tags: [document-conversion, markdown, markitdown, pdf, docx, pptx, csv, excel, large-files]
    related_skills: [ocr-and-documents]
  compatibility:
    agents: [Hermes, Claude Code, Codex, Cursor, OpenAI Agents, generic-agent]
---

# MarkItDown Auto Converter Agent Skill

## Overview

This skill handles explicit document-to-Markdown conversion requests. It uses Microsoft MarkItDown for supported documents and applies conservative size-aware routing so the agent does not accidentally flood its context with enormous Markdown tables or huge converted PDFs.

The skill is intentionally **explicit-trigger only**: a casual file mention should not activate it. It activates when the user asks to convert, export, save, or process a file as Markdown/MD.

## When to Use

Use this skill when the user says something like:

- “把这个 PDF 转成 Markdown”
- “转成 md” / “markdown 处理” / “md 格式看一下”
- “convert this file to markdown”
- “export this report as md”
- “save the document as Markdown”

Do **not** activate this skill for:

- “Analyze this PDF” — use a reading/research workflow.
- “How many rows are in this CSV?” — use Python/pandas directly.
- “Summarize this file” — convert only if Markdown conversion is needed.
- Any unsupported or unsafe file path without first checking existence and permissions.

## Prerequisites

Recommended Python packages:

```bash
python3 -m pip install markitdown pandas openpyxl tabulate
```

Notes:

- `markitdown` is required for PDF/DOCX/PPTX/HTML/EPUB/image conversion.
- `pandas` is required for CSV/Excel summaries.
- `openpyxl` is required for `.xlsx` files.
- `tabulate` improves Markdown table rendering, but the companion script has a fallback if it is unavailable.

## Strategy Matrix

| File type | Size | Strategy |
|---|---:|---|
| PDF | ≤3 MB | Full MarkItDown conversion |
| PDF | 3–30 MB | MarkItDown preview capped to 15,000 characters |
| PDF | >30 MB | Reject full conversion; suggest page-range extraction with PyMuPDF |
| DOCX/PPTX/HTML/EPUB/TXT/RTF | ≤10 MB | Full MarkItDown/direct conversion |
| DOCX/PPTX/HTML/EPUB/TXT/RTF | >10 MB | Preview capped to 15,000 characters |
| CSV | ≤2 MB | pandas summary + first 100 rows as Markdown sample |
| CSV | >2 MB | pandas summary only; never dump full table |
| XLS/XLSX | ≤2 MB | MarkItDown or pandas summary depending on reliability |
| XLS/XLSX | >2 MB | pandas summary only |
| Images | any reasonable size | MarkItDown OCR with quality warning |
| Any file | >1 GB | Reject; suggest streaming tools, DuckDB, SQLite, or chunking |

## Core Workflow

1. **Confirm explicit conversion intent.** If the phrase is ambiguous, ask whether the user wants Markdown conversion.
2. **Resolve and validate the file path/URL.** For local files, check that the file exists and is readable.
3. **Run the companion script when available:**

```bash
python3 scripts/convert_and_verify.py --file "$FILEPATH" --output /tmp/markitdown_output.md
```

4. **Inspect the script result.** It prints file path, size, selected strategy, reason, and output path.
5. **Return the Markdown file or a concise preview.** Do not paste very large Markdown into chat unless the user explicitly requests it.
6. **For failures, provide a fallback.** Examples: PyMuPDF page extraction, pandas sampling, DuckDB queries, OCR workflow.

## Large-Table Rule

Never convert large CSV/Excel files into full Markdown tables. Markdown table syntax expands raw tabular data by roughly 3–5×, quickly exceeding model context windows and making analysis worse. For large tables, provide:

- shape and column names
- dtypes
- missing-value profile
- numeric summary statistics
- first few rows
- optional targeted queries requested by the user

## Companion Script

This repository includes:

```text
scripts/convert_and_verify.py
```

Example:

```bash
python3 scripts/convert_and_verify.py --file report.pdf --output /tmp/report.md
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/data_summary.md
```

Expected console output:

```text
FILE: /absolute/path/report.pdf
SIZE: 2.80 MB
STRATEGY: markitdown_full
REASON: PDF 2.8 MB ≤ 3 MB. Full Markdown conversion.
OK: Markdown generated, 145000 chars, output to /tmp/report.md
```

## Compatibility Notes for Agents

- **Hermes**: copy `skills/productivity/markitdown-auto-converter-agent-skill/` into `~/.hermes/skills/productivity/`.
- **Claude Code**: `CLAUDE.md` points to the canonical root `SKILL.md`.
- **Codex / OpenAI agents**: `AGENTS.md` points to `SKILL.md` and the companion script.
- **Cursor**: use `.cursor/rules/markitdown-auto-converter.mdc` or `.cursorrules`.
- **Generic agents**: root `SKILL.md` is authoritative.

## Common Pitfalls

1. **False trigger** — do not activate for casual file mentions.
2. **Huge Markdown tables** — CSV/Excel >2 MB must be summarized, not fully converted.
3. **Scanned PDFs** — OCR may misread financial figures; warn the user to verify key numbers.
4. **Missing dependencies** — if `markitdown` or `pandas` is absent, report exact install commands.
5. **Context flooding** — save large outputs as `.md` files and return paths/previews.
6. **Formula loss in Excel** — converted output usually contains computed values, not formula logic.
7. **Assuming conversion equals correctness** — tables, footnotes, and OCR may need manual verification.

## Verification Checklist

- [ ] Explicit Markdown conversion intent confirmed
- [ ] File exists, is readable, and extension is supported
- [ ] Size-based strategy selected and reported
- [ ] Large CSV/Excel did not produce a full Markdown table
- [ ] Output file path is returned when content is large
- [ ] OCR/table risks are disclosed when relevant
- [ ] Failure includes an actionable fallback
