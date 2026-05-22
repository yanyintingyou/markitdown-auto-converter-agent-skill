# MarkItDown Auto Converter Agent Skill

A Hermes Agent skill that automatically converts documents to Markdown via `microsoft/markitdown`, with intelligent size-based routing for large tabular files.

---

## Short Description

**Smart document-to-Markdown conversion for Hermes Agent. Routes small files through markitdown, large CSVs/Excel through pandas summaries, and rejects oversized files with actionable alternatives.**

---

## Features

- **Explicit trigger only** — Activates on clear user intent (e.g. "转成markdown", "convert to markdown"), avoiding false positives from casual file mentions.
- **Automatic size-based routing** — No need to manually choose tools; the skill picks the right strategy.
- **Small documents** (PDF ≤3 MB, Word/PPT/HTML ≤10 MB) → Full Markdown conversion via markitdown.
- **Medium documents** (PDF 3–30 MB, Word/PPT >10 MB) → Preview mode (first N pages / 15,000 chars) to prevent context overflow.
- **Large tables** (CSV/Excel >2 MB) → **Rejects full Markdown table conversion**; generates a pandas data exploration summary (shape, dtypes, stats, sample rows) instead.
- **Oversized files** (>1 GB) → Rejected with suggestions (streaming tools, databases, filtered queries).
- **Standalone script included** — `convert_and_verify.py` can be run independently in the terminal.
- **OCR support** — Images (PNG, JPG, etc.) converted via markitdown OCR, with quality warnings for scanned documents.

---

## Why Not Convert Everything to Markdown?

Markdown tables inflate 3–5× compared to raw CSV due to `| col1 | col2 | ... |\n` syntax overhead. A 2 MB CSV (~20,000 rows) becomes ~6–10 MB Markdown, which already pushes LLM context limits. A 10 MB CSV would be ~30–50 MB Markdown — impossible to fit into any model's context window.

This skill solves that by switching to **pandas data exploration summaries** for large tabular files: the agent sees structure, statistics, and a small sample, without drowning in a million-row Markdown table.

---

## Installation

### 1. Dependencies

```bash
pip install markitdown pandas
```

Verify:
```bash
markitdown --version
python3 -c "import pandas; print(pandas.__version__)"
```

### 2. As a Hermes Skill

Copy the skill directory into your Hermes skills repo:

```bash
cp -r markitdown-auto-converter-agent-skill ~/.hermes/skills/productivity/
# or within your own skill tap repo:
# cp -r markitdown-auto-converter-agent-skill skills/productivity/
```

The skill auto-registers on the next Hermes session.

---

## Usage

### In Hermes Agent

Trigger by explicitly requesting Markdown conversion:

```
把这份年报转成 Markdown
```
```
Convert this report.pdf to markdown
```
```
MD 格式处理这个 CSV
```

The skill will:
1. Check file size and extension.
2. Route to the appropriate strategy (full / preview / pandas summary / reject).
3. Return the output or a rejection message with alternatives.

### Standalone Script

```bash
# Pre-check and auto-convert
python3 scripts/convert_and_verify.py --file report.pdf

# Custom output path
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/result.md
```

Example output:
```
FILE: /home/user/report.pdf
SIZE: 2.80 MB
STRATEGY: markitdown_full
REASON: PDF 2.8 MB ≤ 3 MB threshold, full Markdown conversion.
OK: Markdown generated, 145,000 chars, output to /tmp/markitdown_output.md
```

---

## Supported File Types & Thresholds

| Extension | Type | Full Convert | Preview / Reject Threshold | Fallback |
|-----------|------|-------------|---------------------------|----------|
| `.pdf` | PDF | ≤3 MB | 3–30 MB: first 20 pages + TOC; >30 MB: reject | PyMuPDF |
| `.docx` | Word | ≤10 MB | >10 MB: TOC + 5,000 chars | — |
| `.pptx` | PowerPoint | ≤10 MB | >10 MB: first 10 slides + outline | — |
| `.html` `.htm` | HTML | ≤10 MB | >10 MB: headings + 2,000 chars | — |
| `.epub` | EPub | ≤10 MB | >10 MB: TOC + first 3 chapters | — |
| `.xlsx` `.xls` | Excel | ≤2 MB | >2 MB: pandas summary only | openpyxl |
| `.csv` | CSV | ≤2 MB | >2 MB: pandas summary ONLY | pandas |
| `.txt` `.rtf` | Plain text | ≤10 MB | >10 MB: first 5,000 chars | — |
| `.png` `.jpg` `.jpeg` `.tiff` `.bmp` `.gif` | Image | Any size | >50 MB: OCR memory warning | ocr-and-documents skill |

---

## Trigger Keywords

The skill activates when the user explicitly says any of the following (case-insensitive):

- 转成markdown / 转成md / 转md
- markdown处理 / md格式处理 / md 格式看一下
- convert to markdown / process as md
- export to markdown / save as md

**Does NOT trigger on:** "analyze this PDF", "read this file", "how many rows in this CSV" — these are handled by general agent logic or other skills.

---

## Project Structure

```
markitdown-auto-converter-agent-skill/
├── LICENSE
├── README.md
├── .gitignore
└── skills/
    └── markitdown-auto-converter-agent-skill/
        ├── SKILL.md 
        └── scripts/
            └── convert_and_verify.py
```

---

## Design Notes

- **Conservative thresholds**: PDF full-conversion capped at 3 MB because markitdown can OOM on larger files. CSV/Excel table conversion capped at 2 MB because Markdown table inflation quickly exceeds LLM context windows.
- **Fail gracefully**: Every rejection includes an actionable alternative (PyMuPDF, pandas, streaming tools).
- **No API keys**: Pure local tooling. No external tokens consumed.
- **Idempotent**: Running the script multiple times on the same file produces the same strategy decision.

---

## License

MIT
