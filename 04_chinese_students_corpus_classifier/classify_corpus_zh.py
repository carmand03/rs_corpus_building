#!/usr/bin/env python3
"""Resumable LLM classifier for historical newspaper articles.

Version 4 codebook update:
- The HIGHLY_RELEVANT category now includes articles where U.S.-educated Chinese
  appear alongside other foreign-educated Chinese actors.
- Any article that mentions an American-educated / American-returned Chinese
  person is HIGHLY_RELEVANT, including articles about that person's post-return
  career, office, role, association, or public activity.
- The LESS_RELEVANT category remains for Chinese study abroad / returned students
  generally when no American-educated Chinese actor is present.

Modes:
  --provider openai  uses OpenAI API structured outputs
  --provider ollama  uses local Ollama structured outputs

Writes one JSON line per classified article after every successful call.
Safe to interrupt with Ctrl-C and resume: already-classified DocIds are skipped.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm

Label = Literal[
    "HIGHLY_RELEVANT_US_CHINESE_STUDENTS",
    "LESS_RELEVANT_STUDY_ABROAD_GENERAL",
    "IRRELEVANT",
]


class LLMClassification(BaseModel):
    label: Label
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=900)
    evidence_terms: list[str] = Field(default_factory=list)
    needs_review: bool


class SavedClassification(LLMClassification):
    doc_id: str


SCHEMA = LLMClassification.model_json_schema()

SYSTEM_PROMPT = """You are classifying historical newspaper articles for a scholarly corpus on Chinese students educated in the United States. Follow this revised codebook strictly.

Research goal:
Build an exhaustive corpus on Chinese students educated in the United States while preserving a broader contextual layer on Chinese study abroad, returned students, and foreign-educated Chinese people.

Core methodological shift in this version:
HIGHLY_RELEVANT is actor-based as well as topic-based. If an article contains an American-educated Chinese actor, American-returned student, or U.S.-educated Chinese group, classify it as HIGHLY_RELEVANT_US_CHINESE_STUDENTS even if the main story is about the person's later career, office, association, political activity, professional dispute, dinner, election, appointment, or public role rather than about studying in America itself.

Labels:

A. HIGHLY_RELEVANT_US_CHINESE_STUDENTS
Use when the article contains Chinese people, students, pupils, scholars, graduates, professionals, officials, reformers, educational missions, returned students, or returned-student organizations whose education, training, or identity is explicitly connected to the United States, America, or American institutions.

HIGH requires:
1. a Chinese person/group/student/professional/returned-student cue; and
2. a U.S./American education, training, institution, or returned-from-America cue.

The U.S.-educated person or group does NOT need to be the only subject of the article. The article may be about post-return career, political role, official appointment, organizational activity, public speech, social event, professional conflict, reform activity, or local news.

Examples of HIGH:
- Chinese students in America or the United States.
- Chinese students sent to America.
- Chinese graduates of American universities or colleges.
- American-educated Chinese officials, magistrates, doctors, engineers, teachers, reformers, merchants, soldiers, activists, or public figures, including articles about their post-return careers and public activities.
- An American-returned student elected to an office, appointed to a post, leading an association, speaking at a meeting, organizing a corps, or appearing in local/personal/news brevities.
- Returned students from America.
- Chinese Students' Alliance, Chinese Students' Christian Association, or Chinese student clubs in America.
- Boxer Indemnity articles specifically about Chinese students sent to, studying in, or returning from the United States.
- Articles that discuss American-educated Chinese alongside Japanese-, British-, European-, or other foreign-educated Chinese actors.
- Euro-American returned-student organizations or events when American-returned Chinese students are named, discussed, or clearly part of the organization/event.

Calibration examples for HIGH:
- DocId 1371519349: HIGH, because it discusses American-educated liberals in China, even though it contrasts them with Japanese-educated officials and broader foreign-education issues.
- DocId 1759709613: HIGH if the text indicates American-returned students are actors in the Euro-American Returned Students' Union or event; do not downgrade merely because European-returned students are also included.
- DocId 1322117985: HIGH, because it mentions an American-returned student who is now a magistrate and head of the Merchant Volunteer Corps; post-return career articles count when the American-educated Chinese actor is identifiable.

B. LESS_RELEVANT_STUDY_ABROAD_GENERAL
Use when the article concerns the broader ecosystem of Chinese overseas education, study abroad, returned students, foreign-educated Chinese professionals, or institutions/policies/funding that support study abroad, but it does NOT contain an explicit American/U.S.-educated Chinese actor, group, or institution.

Important correction:
Do NOT classify articles as IRRELEVANT merely because they do not mention the United States. If the article discusses Chinese study abroad generally, returned students, foreign-educated Chinese professionals, returned-student organizations, scholarships, loans, indemnity funds, educational missions abroad, or study-abroad policy, classify it as LESS_RELEVANT_STUDY_ABROAD_GENERAL unless an American/U.S.-educated Chinese actor, group, or institution is present, in which case classify it as HIGHLY_RELEVANT_US_CHINESE_STUDENTS.

Examples of LESS:
- Returned-student organizations where the text does not indicate American-returned students or U.S.-educated Chinese actors.
- Disputes, credentials, appointments, or professional conflicts involving foreign-educated Chinese doctors, engineers, lawyers, teachers, officials, or other professionals when the country of education is non-U.S. or unspecified.
- Loans, scholarships, Boxer Indemnity funds, government programs, selection exams, or institutional arrangements for sending Chinese students abroad when the U.S. is not specified.
- Chinese students in Britain, Europe, Japan, France, Germany, Russia, or foreign countries generally, with no American/U.S. education cue.
- Returned students where the country of education is unspecified or mixed and no American-returned actor is identifiable.

Calibration examples for LESS:
- Dispute between foreign-educated doctors and Chinese doctors: LESS if their foreign education is unspecified or non-U.S.; HIGH if the doctors are described as American-educated or American-returned.
- British loan for study abroad: LESS, because it concerns financing/infrastructure for Chinese overseas education but not U.S.-educated Chinese specifically.

C. IRRELEVANT
Use only when the article does not meaningfully concern Chinese overseas education, returned students, study-abroad policy, or foreign-educated Chinese people.

Examples of IRRELEVANT:
- Americans returning to or from China or elsewhere, with no Chinese study-abroad angle.
- Non-Chinese people educated in America.
- Foreigners, missionaries, diplomats, tourists, merchants, soldiers, or athletes in China with no Chinese education or study-abroad angle.
- Generic politics, commerce, war, travel, shipping, sports, crime, society news, or diplomacy with no Chinese overseas education content.
- OCR false positives where Chinese, student, America, foreign, or returned appear incidentally.

Decision rules:
1. First ask: Does the article mention an American-educated Chinese person, American-returned student, U.S.-educated Chinese group, or Chinese student connection to America? If yes, classify HIGH.
2. This HIGH rule applies even when U.S.-educated Chinese are discussed alongside Japanese-, British-, European-, or other foreign-educated Chinese people.
3. This HIGH rule also applies when the article is mainly about post-return career, office, title, social activity, public role, organizational participation, or local/personal news rather than education itself.
4. If there is no American/U.S.-educated Chinese actor, ask: Is this about Chinese overseas education, returned students, or foreign-educated Chinese people generally? If yes, classify LESS.
5. If no meaningful Chinese overseas education / returned-student / foreign-educated Chinese content exists, classify IRRELEVANT.
6. Boxer Indemnity: U.S.-specific student content is HIGH; generic or non-U.S. study-abroad student content is LESS; no meaningful student/education content is IRRELEVANT.
7. If OCR is poor but there are credible clues for American-educated Chinese, use HIGH with lower confidence and needs_review=true. If there are credible clues only for Chinese foreign education generally, use LESS with lower confidence and needs_review=true.
8. When in doubt between HIGH and LESS, choose HIGH if any identifiable Chinese actor/group is linked to American/U.S. education, training, institutions, or return from America.
9. When in doubt between LESS and IRRELEVANT, choose LESS if there is any meaningful evidence of Chinese study abroad, returned students, foreign education, or foreign-educated Chinese professionals.

Return only JSON matching the schema. Do not include doc_id in the JSON.
"""


def article_prompt(row: pd.Series, max_chars: int = 8000) -> str:
    text = str(row.get("Text", ""))[:max_chars]
    return f"""Classify this newspaper article.

DocId: {row.get('DocId', '')}
Date: {row.get('Date', '')}
Title: {row.get('Title', '')}
Source: {row.get('Source', '')}

Text:
{text}
"""


def load_done(jsonl_path: Path) -> set[str]:
    done: set[str] = set()
    if not jsonl_path.exists():
        return done
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                done.add(str(json.loads(line)["doc_id"]))
            except Exception:
                continue
    return done


def write_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def classify_openai(row: pd.Series, model: str, temperature: float = 0.0) -> LLMClassification:
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": article_prompt(row)},
        ],
        temperature=temperature,
        text={
            "format": {
                "type": "json_schema",
                "name": "classification",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )
    return LLMClassification.model_validate_json(response.output_text)


def classify_ollama(row: pd.Series, model: str, temperature: float = 0.0) -> LLMClassification:
    import ollama

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": article_prompt(row)},
        ],
        format=SCHEMA,
        options={"temperature": temperature},
    )
    return LLMClassification.model_validate_json(response["message"]["content"])


def merge_outputs(input_csv: Path, jsonl_path: Path, output_csv: Path) -> None:
    df = pd.read_csv(input_csv, dtype={"DocId": str})
    records = []
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
    if not records:
        return
    out = pd.DataFrame(records).drop_duplicates("doc_id", keep="last")
    merged = df.merge(out, how="left", left_on="DocId", right_on="doc_id")
    merged.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify historical newspaper articles with a resumable LLM workflow.")
    parser.add_argument("--input", default="shenbao_exp_ft.csv")
    parser.add_argument("--output-dir", default="classification_output_zh")
    parser.add_argument("--provider", choices=["openai", "ollama"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--limit", type=int, default=None, help="Use for pilot runs, e.g. --limit 100")
    parser.add_argument("--sleep", type=float, default=0.0, help="Pause between API calls")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--merge-every", type=int, default=25, help="Write merged CSV after this many new classifications")
    parser.add_argument("--max-chars", type=int, default=8000, help="Currently retained for compatibility; prompt uses 8000 by default")
    parser.add_argument(
        "--force-docids",
        default="",
        help="Comma-separated DocIds to reclassify even if already present in the JSONL. The merged CSV keeps the latest record.",
    )
    args = parser.parse_args()

    input_csv = Path(args.input)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    jsonl_path = outdir / f"results_{args.provider}.jsonl"
    output_csv = outdir / f"classified_{args.provider}.csv"
    errors_path = outdir / f"errors_{args.provider}.jsonl"

    model = args.model or ("gpt-4.1-mini" if args.provider == "openai" else "qwen2.5:14b")
    df = pd.read_csv(input_csv, dtype={"DocId": str})
    if args.limit:
        df = df.head(args.limit)

    done = load_done(jsonl_path)
    force_docids = {x.strip() for x in str(args.force_docids).split(",") if x.strip()}
    new_since_merge = 0

    try:
        for _, row in tqdm(df.iterrows(), total=len(df)):
            doc_id = str(row["DocId"])
            if doc_id in done and doc_id not in force_docids:
                continue

            try:
                if args.provider == "openai":
                    llm_result = classify_openai(row, model=model, temperature=args.temperature)
                else:
                    llm_result = classify_ollama(row, model=model, temperature=args.temperature)

                saved = SavedClassification(doc_id=doc_id, **llm_result.model_dump())
                write_jsonl(jsonl_path, saved.model_dump())
                done.add(doc_id)
                force_docids.discard(doc_id)
                new_since_merge += 1

                if new_since_merge >= args.merge_every:
                    merge_outputs(input_csv, jsonl_path, output_csv)
                    new_since_merge = 0

                if args.sleep:
                    time.sleep(args.sleep)

            except (ValidationError, json.JSONDecodeError, Exception) as exc:
                write_jsonl(errors_path, {"doc_id": doc_id, "error": repr(exc)})

    finally:
        merge_outputs(input_csv, jsonl_path, output_csv)
        print(f"Saved JSONL: {jsonl_path}")
        print(f"Merged CSV: {output_csv}")
        print(f"Errors, if any: {errors_path}")


if __name__ == "__main__":
    main()
