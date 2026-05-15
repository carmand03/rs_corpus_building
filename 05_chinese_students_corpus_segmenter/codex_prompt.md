# Codex Prompt for Segmentation Pipeline

Use this prompt inside Codex CLI from the project directory:

```text
You are helping me build a historian-grade segmentation pipeline for OCR newspaper articles.

Read segmentation_codebook.md and segment_articles.py.

Goal: for each ProQuest newspaper document, delineate the largest coherent relevant semantic unit(s) about Chinese students educated in the United States, Chinese study abroad generally, returned students, foreign-educated Chinese professionals, and scholarships/loans/policies.

Important rule: if a long article is coherent and study abroad is only mentioned in passing, keep the whole article. If the document is an OCR/OLR cluster or brevities column, keep only the relevant item(s).

Tasks:
1. Verify that the script is append-only and resumable.
2. Run a dryrun on 5 rows to check files and column names.
3. Help me run a 50-row pilot with OpenAI or Ollama.
4. Inspect rows marked needs_manual_review and suggest codebook refinements.
5. Do not overwrite JSONL results unless I explicitly ask.
```
