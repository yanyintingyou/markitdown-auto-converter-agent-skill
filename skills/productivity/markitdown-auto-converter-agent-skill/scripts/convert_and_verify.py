#!/usr/bin/env python3
"""
markitdown-auto-converter-agent-skill — pre-check and conversion script
Automatically routes files to the correct processing strategy based on type and size.

Usage:
    python3 convert_and_verify.py --file /path/to/document.pdf
    python3 convert_and_verify.py --file /path/to/data.csv --output /tmp/result.md
"""

import argparse
import os
import sys
import subprocess
import shlex

# ---------------------------------------------------------------------------
# Thresholds (MB)
# ---------------------------------------------------------------------------
THRESHOLDS = {
    'pdf_full': 3,          # PDF ≤3 MB: full Markdown
    'pdf_preview': 30,      # PDF 3–30 MB: preview only
    'doc_full': 10,        # Word/HTML/EPub/TXT ≤10 MB: full
    'ppt_full': 10,        # PowerPoint ≤10 MB: full
    'tabular_table': 2,    # CSV/Excel ≤2 MB: Markdown table allowed
    'max_any': 1024,       # Any type >1 GB: reject
}

SUPPORTED_EXTS = {
    '.pdf', '.docx', '.pptx', '.html', '.htm', '.epub',
    '.xlsx', '.xls', '.csv', '.txt', '.rtf',
    '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif',
}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def get_file_info(filepath):
    """Return file metadata dict or (None, error_msg)."""
    if not os.path.exists(filepath):
        return None, f"File not found: {filepath}"
    if not os.path.isfile(filepath):
        return None, f"Path is not a file: {filepath}"
    if not os.access(filepath, os.R_OK):
        return None, f"File not readable: {filepath}"

    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)
    ext = os.path.splitext(filepath)[1].lower()

    return {
        'path': os.path.abspath(filepath),
        'filename': os.path.basename(filepath),
        'size_bytes': size_bytes,
        'size_mb': size_mb,
        'ext': ext,
    }, None


def determine_strategy(info):
    """Return (strategy, reason) based on file metadata."""
    ext = info['ext']
    size = info['size_mb']

    # 0. Global oversized rejection
    if size > THRESHOLDS['max_any']:
        return 'reject_too_large', (
            f"File {size:.1f} MB exceeds {THRESHOLDS['max_any']} MB limit. "
            f"Use polars/duckdb for streaming processing, or load into a database."
        )

    # 1. Unsupported extension
    if ext not in SUPPORTED_EXTS:
        return 'unsupported', (
            f"Unsupported extension: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
        )

    # 2. Images: OCR via markitdown (any size, warn on large images)
    if ext in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}:
        if size > 50:
            return 'markitdown_ocr_warn', (
                f"Image {size:.1f} MB is large; OCR may be slow or memory-intensive."
            )
        return 'markitdown_ocr', "Image file, OCR to Markdown via markitdown."

    # 3. CSV: strict tabular threshold
    if ext == '.csv':
        if size > THRESHOLDS['tabular_table']:
            return 'pandas_summary', (
                f"CSV {size:.1f} MB > {THRESHOLDS['tabular_table']} MB threshold. "
                f"Full Markdown table conversion rejected (3–5x inflation exceeds context window). "
                f"Using pandas data exploration summary instead."
            )
        return 'csv_mixed', (
            f"CSV {size:.1f} MB ≤ {THRESHOLDS['tabular_table']} MB. "
            f"Generating pandas summary + first 100 rows as Markdown table sample."
        )

    # 4. Excel
    if ext in {'.xlsx', '.xls'}:
        if size > THRESHOLDS['tabular_table']:
            return 'pandas_summary', (
                f"Excel {size:.1f} MB > {THRESHOLDS['tabular_table']} MB threshold. "
                f"Using pandas data exploration summary instead of Markdown tables."
            )
        return 'markitdown_full', (
            f"Excel {size:.1f} MB ≤ {THRESHOLDS['tabular_table']} MB. "
            f"Each sheet converted to Markdown table."
        )

    # 5. PDF: tiered
    if ext == '.pdf':
        if size > THRESHOLDS['pdf_preview']:
            return 'reject_or_alternative', (
                f"PDF {size:.1f} MB > {THRESHOLDS['pdf_preview']} MB. "
                f"markitdown may OOM or timeout. Use PyMuPDF for page-range extraction."
            )
        if size > THRESHOLDS['pdf_full']:
            return 'markitdown_preview', (
                f"PDF {size:.1f} MB. Converting first 20 pages + TOC only to avoid context overflow."
            )
        return 'markitdown_full', f"PDF {size:.1f} MB ≤ {THRESHOLDS['pdf_full']} MB. Full Markdown conversion."

    # 6. Word / PPT / HTML / EPub / TXT / RTF
    if ext == '.pptx':
        if size > THRESHOLDS['ppt_full']:
            return 'markitdown_preview', (
                f"PPT {size:.1f} MB > {THRESHOLDS['ppt_full']} MB. "
                f"First 10 slides + outline only."
            )
        return 'markitdown_full', f"PPT {size:.1f} MB. Full Markdown conversion (per slide)."

    if ext in {'.docx', '.html', '.htm', '.epub', '.txt', '.rtf'}:
        if size > THRESHOLDS['doc_full']:
            return 'markitdown_preview', (
                f"{ext} {size:.1f} MB > {THRESHOLDS['doc_full']} MB. "
                f"TOC + first 5,000 chars preview only."
            )
        return 'markitdown_full', f"{ext} {size:.1f} MB. Full Markdown conversion."

    # Fallback
    return 'unsupported', f"Undefined strategy for extension: {ext}"


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------

def exec_markitdown(filepath, output_md, max_chars=None):
    """Run markitdown CLI and optionally truncate output."""
    try:
        result = subprocess.run(
            ['markitdown', filepath],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace',
        )
        if result.returncode != 0:
            return False, f"markitdown error (exit={result.returncode}): {result.stderr[:500]}"

        content = result.stdout
        if max_chars and len(content) > max_chars:
            content = (
                content[:max_chars]
                + f"\n\n...[Content truncated to {max_chars} characters]..."
            )

        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, len(content)

    except subprocess.TimeoutExpired:
        return False, "markitdown timed out (>120 s). File may be too large or malformed."
    except FileNotFoundError:
        return False, "markitdown not installed. Run: pip install markitdown pandas"
    except Exception as e:
        return False, f"markitdown execution error: {str(e)}"


def exec_pandas_summary(filepath, ext, output_md):
    """Generate pandas data exploration summary for CSV / Excel."""
    try:
        import pandas as pd
    except ImportError:
        return False, "pandas not installed. Run: pip install pandas"

    try:
        if ext == '.csv':
            # Fast row count without loading full file
            total_rows = 0
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for _ in f:
                        total_rows += 1
            except Exception:
                total_rows = -1

            df = pd.read_csv(filepath, nrows=5000)

            lines = [
                f"File: {os.path.basename(filepath)}",
                f"Extension: {ext}",
                f"Size: {os.path.getsize(filepath) / (1024 * 1024):.2f} MB",
                f"Estimated total rows: {total_rows:,}" if total_rows >= 0 else "Estimated total rows: unknown",
                f"Sample rows: {len(df)}",
                f"Columns: {len(df.columns)}",
                "",
                "Column names and dtypes:",
                df.dtypes.to_string(),
                "",
            ]

            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            if numeric_cols:
                lines.append("Numeric column statistics:")
                lines.append(df[numeric_cols].describe().to_string())
                lines.append("")

            lines.extend([
                "First 5 rows:",
                df.head().to_string(),
                "",
            ])

            null_rates = df.isnull().mean()
            high_null = null_rates[null_rates > 0.1]
            if not high_null.empty:
                lines.extend([
                    "Columns with null rate >10%:",
                    high_null.to_string(),
                    "",
                ])
            else:
                lines.extend([
                    "Columns with null rate >10%: none",
                    "",
                ])

            cat_cols = df.select_dtypes(include='object').columns.tolist()[:5]
            if cat_cols:
                lines.append("Categorical column unique value counts (first 5 columns):")
                for col in cat_cols:
                    lines.append(f"  {col}: {df[col].nunique()} unique values")
                lines.append("")

        else:  # Excel
            df = pd.read_excel(filepath, nrows=5000)
            lines = [
                f"File: {os.path.basename(filepath)}",
                f"Extension: {ext}",
                f"Size: {os.path.getsize(filepath) / (1024 * 1024):.2f} MB",
                f"Sample rows: {len(df)}",
                f"Columns: {len(df.columns)}",
                "",
                "Column names and dtypes:",
                df.dtypes.to_string(),
                "",
                "Numeric column statistics:",
                df.describe().to_string() if not df.select_dtypes(include='number').empty else "(no numeric columns)",
                "",
                "First 5 rows:",
                df.head().to_string(),
                "",
            ]

        summary = "\n".join(lines)
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(summary)

        return True, len(summary)

    except Exception as e:
        return False, f"pandas processing failed: {str(e)}"


def exec_csv_mixed(filepath, output_md):
    """CSV ≤2 MB: pandas summary + first 100 rows as Markdown table."""
    try:
        import pandas as pd
    except ImportError:
        return False, "pandas not installed"

    try:
        ok, _ = exec_pandas_summary(filepath, '.csv', output_md)
        if not ok:
            return False, "pandas summary generation failed"

        df_sample = pd.read_csv(filepath, nrows=100)
        try:
            md_table = df_sample.to_markdown(index=False)
        except ImportError:
            md_table = df_sample.to_csv(index=False)
            md_table = "`tabulate` is not installed; showing CSV sample instead of Markdown table.\n\n" + md_table

        with open(output_md, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write("First 100 rows as Markdown table sample:\n")
            f.write("(Note: only first 100 rows shown; full table not loaded.)\n\n")
            f.write(md_table)
            f.write("\n")

        return True, os.path.getsize(output_md)

    except Exception as e:
        return False, f"CSV mixed processing failed: {str(e)}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='markitdown-auto-converter pre-check and conversion script')
    parser.add_argument('--file', required=True, help='Input file path')
    parser.add_argument('--intent', default='markdown', help='User intent (reserved)')
    parser.add_argument('--output', default='/tmp/markitdown_output.md', help='Output file path')
    args = parser.parse_args()

    # 1. File metadata
    info, err = get_file_info(args.file)
    if err:
        print(f"ERROR: {err}")
        sys.exit(1)

    print(f"FILE: {info['path']}")
    print(f"SIZE: {info['size_mb']:.2f} MB")

    # 2. Strategy decision
    strategy, reason = determine_strategy(info)
    print(f"STRATEGY: {strategy}")
    print(f"REASON: {reason}")

    # 3. Execute
    if strategy == 'markitdown_full':
        ok, result = exec_markitdown(info['path'], args.output)
        if ok:
            print(f"OK: Markdown generated, {result} chars, output to {args.output}")
        else:
            print(f"ERROR: {result}")
            sys.exit(1)

    elif strategy in ('markitdown_preview', 'markitdown_ocr', 'markitdown_ocr_warn'):
        ok, result = exec_markitdown(info['path'], args.output, max_chars=15000)
        if ok:
            print(f"OK: Markdown preview generated, {result} chars (truncated to 15,000), output to {args.output}")
            if strategy == 'markitdown_ocr_warn':
                print(f"WARN: Large image; OCR quality may vary.")
        else:
            print(f"ERROR: {result}")
            sys.exit(1)

    elif strategy in ('pandas_summary', 'csv_mixed'):
        if strategy == 'csv_mixed':
            ok, result = exec_csv_mixed(info['path'], args.output)
        else:
            ok, result = exec_pandas_summary(info['path'], info['ext'], args.output)
        if ok:
            unit = "bytes" if isinstance(result, int) else "chars"
            print(f"OK: Data exploration summary generated, {result} {unit}, output to {args.output}")
        else:
            print(f"ERROR: {result}")
            sys.exit(1)

    elif strategy == 'reject_or_alternative':
        print(f"WARN: {reason}")
        print("SUGGESTION: Use PyMuPDF for page-range extraction, or specify the section you need.")
        sys.exit(2)

    elif strategy == 'reject_too_large':
        print(f"WARN: {reason}")
        sys.exit(2)

    else:
        print(f"ERROR: {reason}")
        sys.exit(1)


if __name__ == '__main__':
    main()
