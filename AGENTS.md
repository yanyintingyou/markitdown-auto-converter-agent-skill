# Agent Instructions

This repository contains a document-to-Markdown conversion skill. Load and follow `SKILL.md` when the user explicitly asks to convert/export/save/process a file as Markdown or MD.

Important:
1. Do not trigger for casual file mentions.
2. Use `scripts/convert_and_verify.py` when available.
3. Never dump large CSV/Excel files as full Markdown tables; summarize with pandas.
4. For Hermes installation, use `skills/productivity/markitdown-auto-converter-agent-skill/`.
