---
name: markitdown-auto-converter-agent-skill
description: "Use when the user explicitly requests to convert a file to Markdown. Triggers on explicit phrases: '转成markdown', '转成md', '转md', 'markdown处理', 'md格式处理', 'convert to markdown', 'process as md', 'export to markdown', 'save as md'. Automatically detects file type, applies size-appropriate strategy, and routes small documents through markitdown or large tabular files through pandas summary. Not triggered by casual file mentions."
version: 1.0.0
author: yanyintingyou
license: MIT
metadata:
  hermes:
    tags: [document-conversion, markdown, pdf, docx, csv, large-files]
    related_skills: [ocr-and-documents]
---

# MarkItDown Auto Converter Agent Skill

## Overview

This skill responds to the user's **explicit Markdown conversion request** and automatically selects the optimal processing strategy based on file type and size:

- **Small documents** (PDF/Word/PPT/HTML up to size limits): Converted to structured Markdown via `microsoft/markitdown`.
- **Medium documents**: Converted but truncated to preview (first N pages / first 15,000 chars) to avoid context overflow.
- **Large tabular files** (CSV/Excel exceeding the table threshold): **Full Markdown table conversion is rejected**; a pandas data exploration summary is generated instead.
- **Oversized files** (>1GB): Rejected with a suggestion to use streaming tools or databases.

**Core value:** When the user says "convert to Markdown", the agent does not need to worry about file size, format compatibility, or tool selection — the skill does the right thing automatically.

---

## When to Use

**Explicit triggers (user must express conversion intent):**

- "把这份 PDF 转成 Markdown"
- "转 md 处理"
- "用 markdown 格式提取这个 Word"
- "convert this file to markdown"
- "process this document as md"
- "md 格式看一下这个文件"
- "export to markdown"
- "save as md"

**Does NOT trigger (even if a file is mentioned without conversion intent):**

- "I read a PDF yesterday" — casual mention, no conversion needed.
- "Analyze this annual report" — handled by `listed-company-research`; this skill does not intercept.
- "Read this file for me" — if the user does not explicitly say "convert to Markdown", handled by general logic.
- "How many rows in this CSV?" — answered by direct Python scripting, not via this skill.

---

## Prerequisites

**Required packages:**

```bash
pip install markitdown pandas
```

**Verify installation:**

```bash
markitdown --version
python3 -c "import pandas; print(pandas.__version__)"
```

---

## Supported File Types and Strategy Matrix

| Extension | Type | Size Threshold | Strategy |
|-----------|------|---------------|----------|
| `.pdf` | PDF | ≤3 MB: full Markdown; 3–30 MB: first 20 pages + TOC only; >30 MB: reject, suggest PyMuPDF | markitdown |
| `.docx` | Word | ≤10 MB: full Markdown; >10 MB: TOC + first 5,000 chars preview | markitdown |
| `.pptx` | PowerPoint | ≤10 MB: full Markdown (per slide); >10 MB: first 10 slides + outline | markitdown |
| `.html` `.htm` | HTML | ≤10 MB: body to Markdown; >10 MB: heading hierarchy + first 2,000 chars | markitdown |
| `.epub` | EPub | ≤10 MB: chapters to Markdown; >10 MB: TOC + first 3 chapters | markitdown |
| `.xlsx` `.xls` | Excel | ≤2 MB: each sheet as Markdown table; >2 MB: pandas summary only (shape, dtypes, stats) | markitdown / pandas |
| `.csv` | CSV | ≤2 MB: first 100 rows as Markdown table + pandas summary; **>2 MB: pandas summary ONLY**, no Markdown table | pandas summary |
| `.txt` `.rtf` | Plain text | ≤10 MB: direct read; >10 MB: first 5,000 chars | direct read |
| `.png` `.jpg` `.jpeg` `.tiff` `.bmp` `.gif` | Image | Any size: markitdown OCR to Markdown (quality depends on OCR backend) | markitdown OCR |

**Why CSV/Excel >2 MB is rejected for full Markdown table conversion:**

A Markdown table inflates 3–5× compared to raw CSV due to `| col1 | col2 | ... |\n` syntax overhead. A 2 MB CSV (~20,000 rows) becomes ~6–10 MB Markdown, which is already near the practical limit for LLM context windows (typically 128K–200K tokens). Anything larger will either truncate mid-table or crash the context. Hence, the skill switches to a **pandas data exploration summary** — showing structure, statistics, and a small sample — rather than dumping the entire table into Markdown.

---

## Core Workflow

### Step 1: Confirm User Intent

- Check whether user input matches trigger keywords ("转成 markdown", "转 md", "convert to markdown", etc.).
- If confidence is low, **ask for confirmation**: "Do you want to convert this file to Markdown format?"
- If no match, return to general handling without activating this skill.

### Step 2: File Pre-Check (Script Auto-Run)

```bash
python3 scripts/convert_and_verify.py --file "$FILEPATH" --intent markdown
```

Pre-check items:
- [ ] File exists and is readable.
- [ ] File extension is in the supported list.
- [ ] File size in MB.
- [ ] Route to the appropriate processing strategy based on size.

### Step 3: Execute by Strategy

**Strategy A — Small document full conversion (≤ thresholds)**

```bash
markitdown "$FILEPATH" > /tmp/markitdown_output.md
```

**Strategy B — Medium document preview (between full and reject thresholds)**

```bash
markitdown "$FILEPATH" > /tmp/output_full.md
# Script auto-truncates to first N pages / first 15,000 chars + heading structure
```

**Strategy C — Large tabular data exploration (>2 MB CSV/Excel)**

```python
import pandas as pd

# Sample read (does not load entire table into memory)
df = pd.read_csv(filepath, nrows=5000)

summary = f"""
File: {filename}
Size: {size_mb:.1f} MB
Estimated total rows: {total_rows:,}
Columns: {len(df.columns)}
Column names and dtypes:
{df.dtypes.to_string()}

Numeric column statistics:
{df.describe().to_string()}

First 5 rows:
{df.head().to_string()}

Columns with null rate >10%:
{df.isnull().mean()[df.isnull().mean()>0.1].to_string()}
"""
```

**Strategy D — Oversized file rejection (>1 GB any type)**

```
⚠️ File size is X GB, exceeding this skill's processing limit.
Suggestions:
1. For structural analysis, use Python/polars streaming inspection.
2. For full-text reading, consider splitting the file or importing into SQLite/DuckDB.
3. For specific columns/rows, tell me the filter criteria and I will write code.
```

### Step 4: Deliver Output

| Strategy | Deliverable |
|----------|-------------|
| A | Full Markdown content (or saved as `.md` file path) |
| B | Markdown preview (first N pages + TOC, with truncation noted) |
| C | Pandas data exploration summary report (plain text, with stats and samples) |
| D | Rejection reason + alternative suggestions |

---

## Companion Script Usage

`scripts/convert_and_verify.py` is invoked internally by the skill and can also be run standalone in the terminal.

### Standalone Usage

```bash
# Pre-check and auto-execute
python3 scripts/convert_and_verify.py --file report.pdf

# Manual output path
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/result.md
```

**Expected output:**

```
FILE: /path/to/report.pdf
SIZE: 2.80 MB
STRATEGY: markitdown_full
REASON: PDF 2.8 MB ≤ 3 MB threshold, full Markdown conversion.
OK: Markdown generated, 145,000 chars, output to /tmp/markitdown_output.md
```

---

## Error Handling Quick Reference

| Scenario | Handling |
|----------|----------|
| `markitdown` not installed | Prompt `pip install markitdown pandas`, or ask if user prefers `pymupdf` fallback. |
| Unsupported file format | Return "Unsupported format: .xxx", list available formats. |
| Scanned PDF without text layer | Warn: "Scanned PDF; OCR may misread digits/punctuation. Verify key numbers against the original." |
| Empty conversion output | Check if file is corrupted; try `pymupdf` fallback. |
| markitdown timeout (>120 s) | File may be too large or malformed; suggest segmented extraction. |
| Markdown table formatting broken | Warn: "Table structure may have been damaged during conversion. Use pandas to read precise data." |
| File path contains spaces | Script auto-handles via `shlex.quote()`; no user action needed. |

---

## Common Pitfalls

1. **User says "process" without "convert to Markdown"**. This skill activates **only** on explicit conversion intent. If the user says "process this CSV", use general data-analysis logic, not this skill.

2. **Dumping a full CSV table into Markdown**. This is the most common misuse. The script's `pandas_summary` strategy prevents it. **CSV/Excel >2 MB never generates a full Markdown table.**

3. **Excel multi-sheet + formula scenarios**. markitdown converts each sheet to a Markdown table, but formulas are lost (only computed values remain). Excel >2 MB should use pandas summary; if formulas must be inspected, use `openpyxl` directly.

4. **Scanned PDF OCR digit errors**. For financial documents, markitdown OCR may misread `1,234.56` as `1.234.56` or `1234.56`. Critical numbers must be manually verified. If OCR quality is poor, prompt the user to use the `ocr-and-documents` skill with tesseract/pymupdf.

5. **markitdown timeout without feedback**. PDFs >30 MB may cause markitdown to hang. The script sets a 120-second timeout and explicitly warns, suggesting alternatives.

6. **Temporary files not cleaned up**. The script writes to `/tmp/markitdown_output.md`. After skill execution, run `rm -f /tmp/markitdown_output.md /tmp/output_full.md`.

7. **Treating pandas summary as "original source"**. pandas `describe()` is a statistical inference, not the original file content. Cite it as "based on pandas data exploration summary."

8. **Ignoring Markdown output context size**. Even a small file can produce >200 KB Markdown (~50K tokens). The agent should read the first 5,000 characters to judge content type before deciding whether to load the full content.

---

## Verification Checklist

- [ ] User explicitly expressed "convert to Markdown" intent (matches trigger keyword list).
- [ ] File exists and extension is in the supported list.
- [ ] `scripts/convert_and_verify.py` executed and returned a strategy decision.
- [ ] File size assessed; does not exceed the corresponding type threshold.
- [ ] If large CSV/Excel: pandas summary path used; no giant Markdown table was generated.
- [ ] If small document: markitdown output is non-empty and character count is reasonable (>0 and <200 KB or paginated).
- [ ] Scanned PDF OCR quality risk was warned.
- [ ] Output contains original file path, size, strategy type, and timestamp.
- [ ] Temporary files cleaned up.
- [ ] If conversion failed, a fallback was provided (pymupdf / pandas / manual handling suggestion).
