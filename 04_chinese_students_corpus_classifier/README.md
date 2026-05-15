# Chinese students corpus classifier

This version revises the codebook so that the `LESS_RELEVANT_STUDY_ABROAD_GENERAL` category includes:

- returned-student organizations, such as the Euro-American Returned Students' Union;
- foreign-educated Chinese professionals, including doctors and other professional disputes;
- study-abroad loans, scholarships, indemnity funds, and educational missions;
- Chinese study abroad in Britain, Europe, Japan, France, Germany, Russia, or unspecified foreign countries.

The main correction is: do not mark an article irrelevant merely because it lacks a U.S. connection. If it concerns the broader Chinese study-abroad / returned-student ecosystem, classify it as LESS.

## Setup on macOS

```bash
cd chinese_students_corpus_classifier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## OpenAI API mode

```bash
export OPENAI_API_KEY="your_api_key_here"
python classify_corpus.py --provider openai --model gpt-4.1-mini --input proquest_exp_ft.csv --limit 100
```

Full run:

```bash
python classify_corpus.py --provider openai --model gpt-4.1-mini --input proquest_exp_ft.csv
```

## Local Ollama mode

Install Ollama and pull a model, for example:

```bash
ollama pull qwen2.5:14b
python classify_corpus.py --provider ollama --model qwen2.5:14b --input proquest_exp_ft.csv --limit 100
```

## Resume behavior

The script writes one completed article per line to:

```text
classification_output/results_openai.jsonl
```

or:

```text
classification_output/results_ollama.jsonl
```

You may stop the run with `Ctrl-C`. When you rerun the same command, the script skips any `DocId` already present in the JSONL file.

A merged CSV is periodically written to:

```text
classification_output/classified_openai.csv
```

or:

```text
classification_output/classified_ollama.csv
```

## Statistical summaries and visualizations

After you have classification results, generate summary tables, plots, and a Markdown report:

```bash
python analyze_results.py \
  --classified-csv classification_output_en/classified_openai.csv \
  --output-dir classification_analysis_openai
```

You can also analyze directly from the resumable JSONL file:

```bash
python analyze_results.py \
  --jsonl classification_output/results_openai.jsonl \
  --original-csv proquest_exp_ft.csv \
  --output-dir classification_analysis_openai
```

The analysis script creates:

```text
classification_analysis_openai/analysis_report.md
classification_analysis_openai/tables/label_counts.csv
classification_analysis_openai/tables/confidence_by_label.csv
classification_analysis_openai/tables/lowest_confidence_100.csv
classification_analysis_openai/tables/human_review_queue.csv
classification_analysis_openai/tables/label_counts_by_year.csv
classification_analysis_openai/tables/label_counts_by_decade.csv
classification_analysis_openai/tables/top_evidence_terms.csv
classification_analysis_openai/figures/label_counts.png
classification_analysis_openai/figures/confidence_distribution.png
classification_analysis_openai/figures/label_counts_by_decade.png
classification_analysis_openai/figures/top_evidence_terms.png
```

The human-review queue includes all articles flagged by the model with `needs_review=true` plus all articles below the confidence threshold. The default threshold is `0.70`; change it with:

```bash
python analyze_results.py \
  --classified-csv classification_output/classified_openai.csv \
  --review-confidence-threshold 0.80
```

## Codebook update (v4): actor-based HIGH relevance

Version 4 changes the HIGH/LESS boundary:

- If an article mentions an **American-educated Chinese person**, **American-returned student**, **U.S.-educated Chinese group**, or **Chinese student connection to an American institution**, classify it as `HIGHLY_RELEVANT_US_CHINESE_STUDENTS`.
- This applies even when the article focuses on post-return career, public office, local activity, organizational participation, meetings, dinners, or personal news.
- Articles where U.S.-educated Chinese appear alongside Japanese-, British-, European-, or other foreign-educated Chinese should also be HIGH.
- Use `LESS_RELEVANT_STUDY_ABROAD_GENERAL` only when the article concerns Chinese study abroad or returned students generally but **no American/U.S.-educated Chinese actor is identifiable**.

To reclassify only specific already-processed documents, use:

```bash
python classify_corpus.py \
  --provider openai \
  --model gpt-4.1-mini \
  --input proquest_exp_ft.csv \
  --force-docids 1371519349,1759709613,1322117985
```

The JSONL is append-only; the merged CSV keeps the latest record for each `DocId`.
