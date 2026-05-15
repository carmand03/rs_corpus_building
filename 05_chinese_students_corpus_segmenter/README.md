# Chinese Students Newspaper Corpus Segmenter

This package adds a **segmentation stage** after classification. It identifies the largest coherent relevant semantic unit(s) in each OCR/OLR newspaper document.

It is designed for macOS and for interrupted/resumed processing.

## Why segment?

Your ProQuest-style OCR records sometimes contain:

1. one coherent article;
2. multiple unrelated brief news items grouped as one document;
3. improperly segmented OCR/OLR output joining several articles;
4. long articles where Chinese students / study abroad appear only in passing.

The segmentation rule is:

> Keep the largest coherent article/item that contains the relevant study-abroad context. If the whole article is coherent, keep the whole article, even when the topic is only briefly mentioned. If the OCR document is a mixed column or bad segmentation, keep only the relevant item(s).

## Files

- `segmentation_codebook.md` — complete historian-facing codebook.
- `segment_articles.py` — resumable segmenter.
- `requirements.txt` — Python dependencies.

## Setup on macOS

```bash
cd chinese_students_corpus_segmenter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy your input CSV into this folder, or pass its full path.

## Option 1 — Use Codex

Use Codex as the coding/review assistant to run and adapt the pipeline locally.

```bash
cd chinese_students_corpus_segmenter
codex
```

Suggested prompt for Codex:

```text
Read segmentation_codebook.md and segment_articles.py. I am segmenting OCR newspaper articles about Chinese students educated in the United States and Chinese study abroad. Run a 20-document pilot using dryrun first, then prepare an OpenAI or Ollama run. Check that JSONL output is append-only and resumable, and that segments_openai.csv is regenerated from the JSONL. Do not change the codebook without explaining the change.
```

Why use Codex: Codex CLI runs locally in your terminal and can read, edit, and run code in the selected directory. It is useful for adapting column names, adding reports, and inspecting failed rows.

## Option 2 — Use open-source LLMs locally through Ollama

Install Ollama for macOS, then pull a strong instruction-following model. Examples:

```bash
ollama pull qwen3:8b
# or, on a more powerful Mac:
ollama pull qwen3:14b
```

Run a pilot:

```bash
python segment_articles.py \
  --provider ollama \
  --model qwen3:8b \
  --input proquest_exp_ft.csv \
  --limit 50 \
  --output-dir segmentation_output_ollama
```

Full run:

```bash
python segment_articles.py \
  --provider ollama \
  --model qwen3:8b \
  --input proquest_exp_ft.csv \
  --output-dir segmentation_output_ollama
```

The script calls Ollama's local API at `http://localhost:11434/api/generate`. To use another endpoint:

```bash
export OLLAMA_URL="http://localhost:11434/api/generate"
```

## Option 3 — Use OpenAI API

Set your API key:

```bash
export OPENAI_API_KEY="your_key_here"
```

Pilot:

```bash
python segment_articles.py \
  --provider openai \
  --model gpt-4.1-mini \
  --input proquest_exp_ft.csv \
  --limit 100 \
  --output-dir segmentation_output_openai
```

Full run:

```bash
python segment_articles.py \
  --provider openai \
  --model gpt-4.1-mini \
  --input proquest_exp_ft.csv \
  --output-dir segmentation_output_openai
```

If using your previous classification output, pass the prior label column and optionally segment only relevant labels:

```bash
python segment_articles.py \
  --provider openai \
  --model gpt-4.1-mini \
  --input classification_output_v2/classified_openai.csv \
  --prior-label-col label \
  --only-labels HIGHLY_RELEVANT,LESS_RELEVANT_STUDY_ABROAD_GENERAL \
  --output-dir segmentation_output_openai
```

Adjust `--prior-label-col` to the exact column name in your classified CSV.

## Resuming after interruption

The segmenter writes one JSON object per document to:

```text
segmentation_output_openai/segments_openai.jsonl
```

It flushes after every document. If interrupted with `Ctrl-C`, rerun the same command. Completed `DocId`s are skipped.

A flat CSV is regenerated from the JSONL at the end:

```text
segmentation_output_openai/segments_openai.csv
```

## Recommended workflow

1. Run 50–100 documents.
2. Open `segments_openai.csv` in Excel/Numbers.
3. Review all rows where `needs_manual_review = True`.
4. Add your corrections to the codebook as examples.
5. Rerun on the full corpus.

## Output columns

The flat CSV includes:

- `doc_id`
- `segmentation_label`
- `keep_entire_document`
- `overall_boundary_confidence`
- `needs_manual_review`
- `manual_review_reason`
- `segment_index`
- `segment_title`
- `start_anchor`
- `end_anchor`
- `segment_text`
- `topic_type`
- `relevance_to_original_topic`
- `boundary_confidence`
- `boundary_rationale`
- `excluded_content_summary`

## Important caution

For very long documents, `--max-chars` truncates the text sent to the model to control cost/context. Increase it if your chosen model supports longer context.

```bash
python segment_articles.py --provider openai --model gpt-4.1 --input proquest_exp_ft.csv --max-chars 60000
```
