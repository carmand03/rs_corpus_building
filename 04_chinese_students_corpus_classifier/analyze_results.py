#!/usr/bin/env python3
"""Create statistical summaries and visualizations for corpus classification results.

Inputs can be either:
  1. a merged classified CSV produced by classify_corpus.py, or
  2. a results JSONL plus the original input CSV.

Outputs are written to an analysis directory and can be regenerated at any time.
The script is read-only with respect to classification results.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

pip install matplotlib pandas
import matplotlib.pyplot as plt
import pandas as pd

LABEL_ORDER = [
    "HIGHLY_RELEVANT_US_CHINESE_STUDENTS",
    "LESS_RELEVANT_STUDY_ABROAD_GENERAL",
    "IRRELEVANT",
]

LABEL_SHORT = {
    "HIGHLY_RELEVANT_US_CHINESE_STUDENTS": "Highly relevant\nUS Chinese students",
    "LESS_RELEVANT_STUDY_ABROAD_GENERAL": "Less relevant\nstudy abroad general",
    "IRRELEVANT": "Irrelevant",
}


def read_jsonl(path: Path) -> pd.DataFrame:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).drop_duplicates("doc_id", keep="last")


def load_results(classified_csv: Path | None, jsonl: Path | None, original_csv: Path | None) -> pd.DataFrame:
    if classified_csv:
        df = pd.read_csv(classified_csv, dtype={"DocId": str, "doc_id": str})
    elif jsonl and original_csv:
        original = pd.read_csv(original_csv, dtype={"DocId": str})
        results = read_jsonl(jsonl)
        if results.empty:
            raise ValueError(f"No records found in {jsonl}")
        df = original.merge(results, how="right", left_on="DocId", right_on="doc_id")
    else:
        raise ValueError("Provide either --classified-csv OR both --jsonl and --original-csv.")

    if "doc_id" not in df.columns and "DocId" in df.columns:
        df["doc_id"] = df["DocId"].astype(str)
    return df


def safe_year(value) -> int | None:
    if pd.isna(value):
        return None
    text = str(value)
    # Prefer four-digit historical years in the source date field.
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    if match:
        return int(match.group(1))
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.notna(parsed):
        return int(parsed.year)
    return None


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", str(term).strip().lower())


def iter_evidence_terms(series: Iterable) -> Iterable[str]:
    for value in series:
        if pd.isna(value):
            continue
        terms = []
        if isinstance(value, list):
            terms = value
        else:
            text = str(value).strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    terms = parsed
                else:
                    terms = [text]
            except Exception:
                # Handles CSV representations like "['Chinese students', 'America']".
                cleaned = text.strip("[]")
                terms = [t.strip(" '\"") for t in cleaned.split(",")]
        for term in terms:
            norm = normalize_term(term)
            if norm:
                yield norm


def ensure_outdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "tables").mkdir(exist_ok=True)
    (path / "figures").mkdir(exist_ok=True)


def save_label_counts(df: pd.DataFrame, outdir: Path) -> pd.DataFrame:
    total = len(df)
    counts = (
        df["label"]
        .value_counts(dropna=False)
        .rename_axis("label")
        .reset_index(name="n")
    )
    counts["pct"] = counts["n"] / total * 100 if total else 0
    counts["label"] = pd.Categorical(counts["label"], categories=LABEL_ORDER, ordered=True)
    counts = counts.sort_values("label")
    counts.to_csv(outdir / "tables" / "label_counts.csv", index=False)
    return counts


def save_confidence_summary(df: pd.DataFrame, outdir: Path) -> pd.DataFrame:
    if "confidence" not in df.columns:
        return pd.DataFrame()
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    summary = (
        df.groupby("label", dropna=False)["confidence"]
        .agg(n="count", mean="mean", median="median", min="min", max="max")
        .reset_index()
    )
    summary.to_csv(outdir / "tables" / "confidence_by_label.csv", index=False)
    low = df.sort_values("confidence", ascending=True).head(100)
    cols = [c for c in ["doc_id", "DocId", "Date", "Title", "Source", "label", "confidence", "needs_review", "rationale"] if c in low.columns]
    low[cols].to_csv(outdir / "tables" / "lowest_confidence_100.csv", index=False)
    return summary


def save_review_queue(df: pd.DataFrame, outdir: Path, threshold: float) -> pd.DataFrame:
    work = df.copy()
    if "confidence" in work.columns:
        work["confidence"] = pd.to_numeric(work["confidence"], errors="coerce")
    else:
        work["confidence"] = pd.NA
    if "needs_review" in work.columns:
        needs_review = work["needs_review"].astype(str).str.lower().isin(["true", "1", "yes"])
    else:
        needs_review = pd.Series(False, index=work.index)
    review = work[needs_review | (work["confidence"] < threshold)].copy()
    review = review.sort_values(["needs_review", "confidence"], ascending=[False, True])
    cols = [c for c in ["doc_id", "DocId", "Date", "Title", "Source", "label", "confidence", "needs_review", "rationale", "evidence_terms"] if c in review.columns]
    review[cols].to_csv(outdir / "tables" / "human_review_queue.csv", index=False)
    return review


def save_temporal_tables(df: pd.DataFrame, outdir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = df.copy()
    date_col = "Date" if "Date" in work.columns else None
    if date_col is None:
        return pd.DataFrame(), pd.DataFrame()
    work["year"] = work[date_col].apply(safe_year)
    work = work.dropna(subset=["year"])
    if work.empty:
        return pd.DataFrame(), pd.DataFrame()
    work["year"] = work["year"].astype(int)
    work["decade"] = (work["year"] // 10) * 10

    by_year = work.pivot_table(index="year", columns="label", values="doc_id", aggfunc="count", fill_value=0)
    by_year = by_year.reindex(columns=LABEL_ORDER, fill_value=0).reset_index()
    by_year.to_csv(outdir / "tables" / "label_counts_by_year.csv", index=False)

    by_decade = work.pivot_table(index="decade", columns="label", values="doc_id", aggfunc="count", fill_value=0)
    by_decade = by_decade.reindex(columns=LABEL_ORDER, fill_value=0).reset_index()
    by_decade.to_csv(outdir / "tables" / "label_counts_by_decade.csv", index=False)
    return by_year, by_decade


def save_evidence_terms(df: pd.DataFrame, outdir: Path, top_n: int) -> pd.DataFrame:
    if "evidence_terms" not in df.columns:
        return pd.DataFrame()
    counter = Counter(iter_evidence_terms(df["evidence_terms"]))
    terms = pd.DataFrame(counter.most_common(top_n), columns=["term", "n"])
    terms.to_csv(outdir / "tables" / "top_evidence_terms.csv", index=False)
    return terms


def plot_label_counts(counts: pd.DataFrame, outdir: Path) -> None:
    if counts.empty:
        return
    plot_df = counts.copy()
    plot_df["label_short"] = plot_df["label"].map(LABEL_SHORT).fillna(plot_df["label"].astype(str))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(plot_df["label_short"], plot_df["n"])
    ax.set_title("Classification counts")
    ax.set_ylabel("Articles")
    ax.set_xlabel("Label")
    for i, row in plot_df.reset_index(drop=True).iterrows():
        ax.text(i, row["n"], f"{int(row['n'])}\n{row['pct']:.1f}%", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "label_counts.png", dpi=200)
    plt.close(fig)


def plot_confidence(df: pd.DataFrame, outdir: Path) -> None:
    if "confidence" not in df.columns:
        return
    conf = pd.to_numeric(df["confidence"], errors="coerce").dropna()
    if conf.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(conf, bins=20)
    ax.set_title("Confidence distribution")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Articles")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "confidence_distribution.png", dpi=200)
    plt.close(fig)


def plot_by_decade(by_decade: pd.DataFrame, outdir: Path) -> None:
    if by_decade.empty:
        return
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = None
    x = by_decade["decade"].astype(str)
    for label in LABEL_ORDER:
        vals = by_decade[label] if label in by_decade.columns else 0
        ax.bar(x, vals, bottom=bottom, label=LABEL_SHORT.get(label, label).replace("\n", " "))
        bottom = vals if bottom is None else bottom + vals
    ax.set_title("Classification counts by decade")
    ax.set_xlabel("Decade")
    ax.set_ylabel("Articles")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "label_counts_by_decade.png", dpi=200)
    plt.close(fig)


def plot_top_terms(terms: pd.DataFrame, outdir: Path) -> None:
    if terms.empty:
        return
    plot_df = terms.head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(plot_df["term"], plot_df["n"])
    ax.set_title("Top evidence terms")
    ax.set_xlabel("Occurrences")
    ax.set_ylabel("Term")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "top_evidence_terms.png", dpi=200)
    plt.close(fig)


def write_markdown_report(outdir: Path, df: pd.DataFrame, counts: pd.DataFrame, conf: pd.DataFrame, review: pd.DataFrame) -> None:
    lines = []
    lines.append("# Classification analysis report\n")
    lines.append(f"Total classified records analyzed: **{len(df):,}**\n")

    lines.append("## Label distribution\n")
    if not counts.empty:
        lines.append(counts.to_markdown(index=False))
        lines.append("\n![Label counts](figures/label_counts.png)\n")

    lines.append("## Confidence\n")
    if not conf.empty:
        lines.append(conf.to_markdown(index=False))
        lines.append("\n![Confidence distribution](figures/confidence_distribution.png)\n")

    lines.append("## Temporal distribution\n")
    if (outdir / "figures" / "label_counts_by_decade.png").exists():
        lines.append("![Label counts by decade](figures/label_counts_by_decade.png)\n")
    else:
        lines.append("No usable date/year field was found for temporal plots.\n")

    lines.append("## Human review queue\n")
    lines.append(f"Records flagged for review or below the confidence threshold: **{len(review):,}**.\n")
    lines.append("See `tables/human_review_queue.csv`.\n")

    lines.append("## Evidence terms\n")
    if (outdir / "figures" / "top_evidence_terms.png").exists():
        lines.append("![Top evidence terms](figures/top_evidence_terms.png)\n")
    lines.append("Full tables are saved in `tables/`.\n")

    (outdir / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize and visualize classification results.")
    parser.add_argument("--classified-csv", default=None, help="Merged CSV from classify_corpus.py")
    parser.add_argument("--jsonl", default=None, help="Raw results JSONL from classify_corpus.py")
    parser.add_argument("--original-csv", default=None, help="Original ProQuest CSV; required with --jsonl")
    parser.add_argument("--output-dir", default="classification_analysis")
    parser.add_argument("--review-confidence-threshold", type=float, default=0.70)
    parser.add_argument("--top-terms", type=int, default=50)
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    ensure_outdir(outdir)

    df = load_results(
        Path(args.classified_csv) if args.classified_csv else None,
        Path(args.jsonl) if args.jsonl else None,
        Path(args.original_csv) if args.original_csv else None,
    )
    if "label" not in df.columns:
        raise ValueError("The input results do not contain a 'label' column.")

    counts = save_label_counts(df, outdir)
    conf = save_confidence_summary(df, outdir)
    review = save_review_queue(df, outdir, args.review_confidence_threshold)
    _, by_decade = save_temporal_tables(df, outdir)
    terms = save_evidence_terms(df, outdir, args.top_terms)

    plot_label_counts(counts, outdir)
    plot_confidence(df, outdir)
    plot_by_decade(by_decade, outdir)
    plot_top_terms(terms, outdir)
    write_markdown_report(outdir, df, counts, conf, review)

    print(f"Analysis saved to: {outdir}")
    print(f"Report: {outdir / 'analysis_report.md'}")
    print(f"Tables: {outdir / 'tables'}")
    print(f"Figures: {outdir / 'figures'}")


if __name__ == "__main__":
    main()
