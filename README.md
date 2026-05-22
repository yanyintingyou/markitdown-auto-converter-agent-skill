# markitdown-auto-converter-agent-skill

Intelligent auto-converter for turning documents into Markdown with smart size-aware strategies.

Part of the Hermes Agent skill ecosystem.

## Overview

This skill automatically handles Markdown conversion requests by routing files to the optimal processing strategy based on type and size:

- **Small documents** (PDF, Word, PPT, HTML, etc.): Full conversion via `microsoft/markitdown`
- **Medium documents**: Preview mode (first N pages / limited characters) to avoid context overflow
- **Large tabular files** (CSV/Excel > 2MB): Pandas data exploration summary instead of bloated Markdown tables
- **Images**: OCR via markitdown
- **Oversized files** (>1GB): Graceful rejection with suggestions

**Key innovation**: Prevents the common pitfall of Markdown table size explosion (3-5x inflation) that breaks LLM context windows.

## Installation

```bash
pip install markitdown pandas
```

## Usage

### Via Hermes Agent (recommended)

Simply say:
- "把这份 PDF 转成 Markdown"
- "convert this file to markdown"
- "转 md 处理"

The skill will automatically detect the file and apply the best strategy.

### Standalone

```bash
python3 scripts/convert_and_verify.py --file /path/to/document.pdf
python3 scripts/convert_and_verify.py --file data.csv --output /tmp/result.md
```

See `SKILL.md` for full documentation, strategy matrix, and design rationale.

## Supported Formats

PDF, DOCX, PPTX, HTML, EPUB, XLSX/XLS, CSV, TXT, RTF, and images (PNG/JPG/etc with OCR).

## License

MIT License

## Author

yanyintingyou (Tingyou Li)