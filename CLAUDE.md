# Claude Code Instructions

Use `SKILL.md` as the canonical skill definition for this repository. This is a document conversion skill.

When responding:
- Activate only on explicit Markdown conversion intent.
- Prefer the companion script `scripts/convert_and_verify.py`.
- Avoid context flooding; return output paths/previews for large conversions.
