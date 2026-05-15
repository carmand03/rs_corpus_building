#!/usr/bin/env python3
"""
Segment OCR/OLR newspaper documents into the largest coherent relevant semantic unit(s).

Providers:
  - openai: OpenAI Responses API with JSON-schema structured output
  - ollama: local Ollama generate API with JSON schema
  - dryrun: simple heuristic fallback for testing pipeline only

Outputs are append-only JSONL and can be resumed safely.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

SEGMENTATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "doc_id", "segmentation_label", "keep_entire_document", "segments",
        "overall_boundary_confidence", "needs_manual_review", "manual_review_reason"
    ],
    "properties": {
        "doc_id": {"type": "string"},
        "segmentation_label": {"type": "string", "enum": ["WHOLE_DOCUMENT", "SINGLE_SEGMENT", "MULTIPLE_SEGMENTS", "NO_RELEVANT_SEGMENT"]},
        "keep_entire_document": {"type": "boolean"},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "segment_index", "segment_title", "start_anchor", "end_anchor", "segment_text",
                    "topic_type", "relevance_to_original_topic", "boundary_confidence",
                    "boundary_rationale", "excluded_content_summary"
                ],
                "properties": {
                    "segment_index": {"type": "integer"},
                    "segment_title": {"type": "string"},
                    "start_anchor": {"type": "string"},
                    "end_anchor": {"type": "string"},
                    "segment_text": {"type": "string"},
                    "topic_type": {"type": "string", "enum": [
                        "US_EDUCATED_CHINESE", "STUDY_ABROAD_GENERAL", "RETURNED_STUDENTS",
                        "FOREIGN_EDUCATED_PROFESSIONALS", "SCHOLARSHIP_LOAN_POLICY", "OTHER_RELATED"
                    ]},
                    "relevance_to_original_topic": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "boundary_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "boundary_rationale": {"type": "string"},
                    "excluded_content_summary": {"type": "string"}
                }
            }
        },
        "overall_boundary_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "needs_manual_review": {"type": "boolean"},
        "manual_review_reason": {"type": "string"}
    }
}

SEGMENTATION_LABELS = {
    "WHOLE_DOCUMENT", "SINGLE_SEGMENT", "MULTIPLE_SEGMENTS", "NO_RELEVANT_SEGMENT"
}
TOPIC_TYPES = {
    "US_EDUCATED_CHINESE", "STUDY_ABROAD_GENERAL", "RETURNED_STUDENTS",
    "FOREIGN_EDUCATED_PROFESSIONALS", "SCHOLARSHIP_LOAN_POLICY", "OTHER_RELATED"
}
RELEVANCE_LABELS = {"HIGH", "MEDIUM", "LOW"}
BASE_CSV_FIELDS = [
    "doc_id", "segmentation_label", "keep_entire_document",
    "overall_boundary_confidence", "needs_manual_review", "manual_review_reason"
]
SEGMENT_CSV_FIELDS = [
    "segment_index", "segment_title", "start_anchor", "end_anchor", "segment_text",
    "topic_type", "relevance_to_original_topic", "boundary_confidence",
    "boundary_rationale", "excluded_content_summary"
]
CSV_FIELDS = BASE_CSV_FIELDS + SEGMENT_CSV_FIELDS

SYSTEM_PROMPT = """You are a historian's segmentation assistant for OCR/OLR historical newspaper data.
Your task is NOT to summarize. Your task is to delineate the largest semantic unit(s) in a document that contain relevant study-abroad context.

Relevant scope includes: Chinese students educated in the United States; Chinese study abroad generally; returned students; returned-student organizations; foreign-educated Chinese professionals; scholarships, loans, Boxer Indemnity, educational missions, and public debate about overseas education.

Core rule:
- If the document is one coherent article and study abroad/Chinese students are only mentioned in passing, keep the ENTIRE document.
- If the document is an improperly segmented OCR/OLR cluster or a brevities/local/personal-news column, keep only the relevant item(s), not unrelated neighboring items.
- If several separated relevant items appear, return multiple segments.
- Preserve exact text as much as possible; do not modernize OCR.
- Segment boundaries should be continuous spans from the document, not rewritten summaries.

Return only valid JSON matching the provided schema."""

USER_TEMPLATE = """Segment this newspaper document according to the codebook.

Metadata:
DocId: {doc_id}
Date: {date}
Title: {title}
Source: {source}
Prior classification label, if available: {prior_label}

Document text:
{text}
"""

@dataclass
class Config:
    provider: str
    model: str
    input_csv: Path
    output_dir: Path
    output_jsonl: Path
    output_segments_csv: Path
    doc_id_col: str = "DocId"
    text_col: str = "Text"
    title_col: str = "Title"
    date_col: str = "Date"
    source_col: str = "Source"
    prior_label_col: Optional[str] = None
    max_chars: int = 24000
    sleep: float = 0.2
    limit: Optional[int] = None
    only_labels: Optional[List[str]] = None


def load_completed(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("doc_id"):
                    done.add(str(obj["doc_id"]))
            except json.JSONDecodeError:
                continue
    return done


def clean_text(x: Any) -> str:
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()


def build_user_prompt(row: pd.Series, cfg: Config) -> str:
    text = clean_text(row.get(cfg.text_col, ""))
    if len(text) > cfg.max_chars:
        # Keep beginning and end. The model is told to flag uncertainty.
        half = cfg.max_chars // 2
        text = text[:half] + "\n\n[... DOCUMENT TRUNCATED FOR MODEL CONTEXT ...]\n\n" + text[-half:]
    prior = row.get(cfg.prior_label_col, "") if cfg.prior_label_col and cfg.prior_label_col in row else ""
    return USER_TEMPLATE.format(
        doc_id=str(row.get(cfg.doc_id_col, "")),
        date=str(row.get(cfg.date_col, "")),
        title=str(row.get(cfg.title_col, "")),
        source=str(row.get(cfg.source_col, "")),
        prior_label=str(prior),
        text=text,
    )


def call_openai(prompt: str, cfg: Config) -> Dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Run: pip install -r requirements.txt")
    client = OpenAI()
    resp = client.responses.create(
        model=cfg.model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "newspaper_segmentation",
                "strict": True,
                "schema": SEGMENTATION_SCHEMA,
            }
        },
    )
    return json.loads(resp.output_text)


def call_ollama(prompt: str, cfg: Config) -> Dict[str, Any]:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    payload = {
        "model": cfg.model,
        "prompt": SYSTEM_PROMPT + "\n\n" + prompt,
        "format": SEGMENTATION_SCHEMA,
        "stream": False,
        "options": {"temperature": 0},
    }
    r = requests.post(url, json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    return json.loads(data.get("response", "{}"))


def call_dryrun(prompt: str, cfg: Config, row: pd.Series) -> Dict[str, Any]:
    doc_id = str(row.get(cfg.doc_id_col, ""))
    text = clean_text(row.get(cfg.text_col, ""))
    title = str(row.get(cfg.title_col, "Untitled"))
    # Heuristic only: useful for testing IO, not for real segmentation.
    return {
        "doc_id": doc_id,
        "segmentation_label": "WHOLE_DOCUMENT",
        "keep_entire_document": True,
        "segments": [{
            "segment_index": 1,
            "segment_title": title,
            "start_anchor": text[:80],
            "end_anchor": text[-80:],
            "segment_text": text,
            "topic_type": "OTHER_RELATED",
            "relevance_to_original_topic": "MEDIUM",
            "boundary_confidence": 0.2,
            "boundary_rationale": "Dry-run placeholder. Do not use as research output.",
            "excluded_content_summary": "None."
        }],
        "overall_boundary_confidence": 0.2,
        "needs_manual_review": True,
        "manual_review_reason": "Dry-run placeholder."
    }


def validate_and_repair(obj: Dict[str, Any], row: pd.Series, cfg: Config) -> Dict[str, Any]:
    doc_id = str(row.get(cfg.doc_id_col, ""))
    obj["doc_id"] = str(obj.get("doc_id") or doc_id)
    if "segments" not in obj or not isinstance(obj["segments"], list):
        obj["segments"] = []
    confs = []
    original = clean_text(row.get(cfg.text_col, ""))
    title = str(row.get(cfg.title_col, "Untitled") or "Untitled")
    reasons = []
    for i, seg in enumerate(obj["segments"], start=1):
        seg["segment_index"] = int(seg.get("segment_index") or i)
        seg_text = clean_text(seg.get("segment_text", ""))
        seg["segment_text"] = seg_text
        seg["segment_title"] = str(seg.get("segment_title") or title or f"Segment {i}")
        if not seg.get("start_anchor") and seg_text:
            seg["start_anchor"] = seg_text[:80]
        if not seg.get("end_anchor") and seg_text:
            seg["end_anchor"] = seg_text[-80:]
        seg.setdefault("start_anchor", "")
        seg.setdefault("end_anchor", "")
        if seg.get("topic_type") not in TOPIC_TYPES:
            reasons.append(f"segment_{i}_topic_type_repaired")
            seg["topic_type"] = "OTHER_RELATED"
        if seg.get("relevance_to_original_topic") not in RELEVANCE_LABELS:
            reasons.append(f"segment_{i}_relevance_repaired")
            seg["relevance_to_original_topic"] = "MEDIUM"
        try:
            conf = max(0.0, min(1.0, float(seg.get("boundary_confidence", 0))))
        except Exception:
            conf = 0.0
        seg["boundary_confidence"] = conf
        confs.append(conf)
        seg["boundary_rationale"] = str(seg.get("boundary_rationale") or "")
        seg["excluded_content_summary"] = str(seg.get("excluded_content_summary") or "")

    original_label = obj.get("segmentation_label")
    label = original_label if original_label in SEGMENTATION_LABELS else None
    keep_entire = bool(obj.get("keep_entire_document", False))
    if not obj["segments"]:
        label = "NO_RELEVANT_SEGMENT"
        keep_entire = False
    elif label == "WHOLE_DOCUMENT" or keep_entire:
        label = "WHOLE_DOCUMENT"
        keep_entire = True
    elif len(obj["segments"]) == 1:
        label = "SINGLE_SEGMENT"
        keep_entire = False
    else:
        label = "MULTIPLE_SEGMENTS"
        keep_entire = False
    if original_label != label:
        reasons.append(f"segmentation_label_repaired_from_{original_label or 'missing'}")
    obj["segmentation_label"] = label
    obj["keep_entire_document"] = keep_entire

    if confs:
        obj["overall_boundary_confidence"] = min(confs)
    obj.setdefault("overall_boundary_confidence", 0)
    if float(obj.get("overall_boundary_confidence", 0)) < 0.75:
        reasons.append("boundary_confidence_below_0.75")
    if obj.get("segmentation_label") == "MULTIPLE_SEGMENTS":
        reasons.append("multiple_segments")
    for seg in obj["segments"]:
        st = clean_text(seg.get("segment_text", ""))
        if st and st not in original:
            # OCR spacing may differ; flag for audit rather than failing.
            reasons.append(f"segment_{seg.get('segment_index')}_text_not_exact_substring")
            break
    manual = bool(obj.get("needs_manual_review", False)) or bool(reasons)
    obj["needs_manual_review"] = manual
    existing = obj.get("manual_review_reason", "")
    if reasons:
        obj["manual_review_reason"] = (existing + "; " if existing else "") + ", ".join(sorted(set(reasons)))
    else:
        obj.setdefault("manual_review_reason", "")
    return obj


def flatten_segments(jsonl_path: Path, out_csv: Path) -> None:
    rows: List[Dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            base = {k: obj.get(k) for k in [
                "doc_id", "segmentation_label", "keep_entire_document",
                "overall_boundary_confidence", "needs_manual_review", "manual_review_reason"
            ]}
            segments = obj.get("segments", [])
            if not segments:
                row = dict(base)
                row.update({field: "" for field in SEGMENT_CSV_FIELDS})
                rows.append(row)
                continue
            for seg in segments:
                row = dict(base)
                row.update(seg)
                rows.append(row)
    pd.DataFrame(rows, columns=CSV_FIELDS).to_csv(out_csv, index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input CSV, e.g. proquest_exp_ft.csv or classified CSV")
    ap.add_argument("--provider", choices=["openai", "ollama", "dryrun"], default="openai")
    ap.add_argument("--model", default="gpt-4.1-mini")
    ap.add_argument("--output-dir", default="segmentation_output")
    ap.add_argument("--doc-id-col", default="DocId")
    ap.add_argument("--text-col", default="Text")
    ap.add_argument("--title-col", default="Title")
    ap.add_argument("--date-col", default="Date")
    ap.add_argument("--source-col", default="Source")
    ap.add_argument("--prior-label-col", default=None, help="Optional classification label column")
    ap.add_argument("--only-labels", default=None, help="Comma-separated prior labels to segment, e.g. HIGHLY_RELEVANT,LESS_RELEVANT_STUDY_ABROAD_GENERAL")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-chars", type=int, default=24000)
    ap.add_argument("--sleep", type=float, default=0.2)
    args = ap.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = Config(
        provider=args.provider,
        model=args.model,
        input_csv=Path(args.input),
        output_dir=outdir,
        output_jsonl=outdir / f"segments_{args.provider}.jsonl",
        output_segments_csv=outdir / f"segments_{args.provider}.csv",
        doc_id_col=args.doc_id_col,
        text_col=args.text_col,
        title_col=args.title_col,
        date_col=args.date_col,
        source_col=args.source_col,
        prior_label_col=args.prior_label_col,
        max_chars=args.max_chars,
        sleep=args.sleep,
        limit=args.limit,
        only_labels=[x.strip() for x in args.only_labels.split(",")] if args.only_labels else None,
    )

    df = pd.read_csv(cfg.input_csv)
    required_cols = [cfg.doc_id_col, cfg.text_col, cfg.title_col, cfg.date_col, cfg.source_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise SystemExit(f"Input CSV is missing required column(s): {', '.join(missing_cols)}")
    if cfg.only_labels:
        if not cfg.prior_label_col:
            raise SystemExit("--only-labels requires --prior-label-col")
        if cfg.prior_label_col not in df.columns:
            raise SystemExit(f"--prior-label-col '{cfg.prior_label_col}' is not present in the input CSV")
    completed = load_completed(cfg.output_jsonl)
    processed = 0
    print(f"Loaded {len(df)} rows. Already completed: {len(completed)}. Output: {cfg.output_jsonl}")

    with cfg.output_jsonl.open("a", encoding="utf-8") as out:
        for _, row in df.iterrows():
            doc_id = str(row.get(cfg.doc_id_col, ""))
            if not doc_id or doc_id in completed:
                continue
            if cfg.only_labels and cfg.prior_label_col and cfg.prior_label_col in row:
                if str(row.get(cfg.prior_label_col)) not in cfg.only_labels:
                    continue
            prompt = build_user_prompt(row, cfg)
            try:
                if cfg.provider == "openai":
                    obj = call_openai(prompt, cfg)
                elif cfg.provider == "ollama":
                    obj = call_ollama(prompt, cfg)
                else:
                    obj = call_dryrun(prompt, cfg, row)
                obj = validate_and_repair(obj, row, cfg)
                out.write(json.dumps(obj, ensure_ascii=False) + "\n")
                out.flush()
                completed.add(doc_id)
                processed += 1
                print(f"[{processed}] segmented DocId={doc_id} label={obj.get('segmentation_label')} review={obj.get('needs_manual_review')}")
                if cfg.limit and processed >= cfg.limit:
                    break
                time.sleep(cfg.sleep)
            except KeyboardInterrupt:
                print("Interrupted by user. Progress saved to JSONL.", file=sys.stderr)
                break
            except Exception as e:
                err = {
                    "doc_id": doc_id,
                    "segmentation_label": "NO_RELEVANT_SEGMENT",
                    "keep_entire_document": False,
                    "segments": [],
                    "overall_boundary_confidence": 0,
                    "needs_manual_review": True,
                    "manual_review_reason": f"ERROR: {type(e).__name__}: {e}",
                }
                out.write(json.dumps(err, ensure_ascii=False) + "\n")
                out.flush()
                completed.add(doc_id)
                processed += 1
                print(f"ERROR DocId={doc_id}: {e}", file=sys.stderr)
                if cfg.limit and processed >= cfg.limit:
                    break

    flatten_segments(cfg.output_jsonl, cfg.output_segments_csv)
    print(f"Wrote flat segment CSV: {cfg.output_segments_csv}")

if __name__ == "__main__":
    main()
