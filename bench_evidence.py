"""Evaluate whether retrieved chunks contain the evidence needed to answer queries."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from bench import (
    BENCHMARK_QUERIES,
    build_store,
    create_embedder,
    gold_rank,
    load_source_documents,
    preview,
)
from heading_chunker import HeadingRecursiveChunker
from src import FixedSizeChunker, RecursiveChunker, SentenceChunker


# Markers were selected from the gold evidence for the queries currently
# defined in bench.py. A chunk must contain every marker to count as evidence.
EVIDENCE_MARKERS = {
    "Q1": ["Hoàn Tiền Ngay", "vòng 6 ngày"],
    "Q2": ["phí vận chuyển ban đầu", "không được hoàn lại"],
    "Q3": ["video mở kiện hàng", "liên tục"],
    "Q4": ["48 giờ", "hoàn tiền cho khách hàng hoặc đổi sản phẩm"],
    "Q5": ["1 ngày làm việc", "mã vận đơn"],
}


def normalise_text(value: str) -> str:
    """Normalise Unicode case and whitespace for deterministic marker checks."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def contains_evidence(result: dict[str, Any], markers: list[str]) -> bool:
    """Return true only when a retrieved chunk contains all required markers."""
    content = normalise_text(result["content"])
    return all(normalise_text(marker) in content for marker in markers)


def gold_evidence_rank(
    results: list[dict[str, Any]], gold_doc_ids: list[str], markers: list[str]
) -> int | None:
    """Find the first result that is both a gold document and evidence-bearing."""
    gold_ids = set(gold_doc_ids)
    for rank, result in enumerate(results, start=1):
        if result["metadata"].get("doc_id") in gold_ids and contains_evidence(result, markers):
            return rank
    return None


def create_chunker(name: str):
    """Return the requested strategy with the fixed benchmark configuration."""
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50)
    if name == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    if name == "heading":
        return HeadingRecursiveChunker(chunk_size=500)
    return RecursiveChunker(chunk_size=500)


def format_result(rank: int, result: dict[str, Any], markers: list[str]) -> list[str]:
    """Render one ranked retrieval result with an explicit evidence verdict."""
    metadata = result["metadata"]
    return [
        f"TOP {rank}",
        f"score: {result['score']:.6f}",
        f"doc_id: {metadata.get('doc_id', '')}",
        f"title: {metadata.get('title', '')}",
        f"chunk_index: {metadata.get('chunk_index', '')}",
        f"contains all evidence markers: {contains_evidence(result, markers)}",
        f"content preview: {preview(result['content'])}",
        "",
    ]


def score_from_rank(rank: int | None) -> int:
    """Score rank one as two, ranks two or three as one, otherwise zero."""
    if rank == 1:
        return 2
    if rank in {2, 3}:
        return 1
    return 0


def run_strategy(strategy: str, embedding_name: str, top_k: int) -> tuple[list[str], dict[str, int]]:
    """Run one chunking strategy against all benchmark queries."""
    documents = load_source_documents()
    embedder = create_embedder(embedding_name)
    store, chunk_count = build_store(documents, create_chunker(strategy), embedder)
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    lines = [
        f"EVIDENCE BENCHMARK: {strategy}",
        f"embedding backend: {embedding_name} ({backend_name})",
        f"source documents: {len(documents)}",
        f"chunks: {chunk_count}",
        f"top_k: {top_k}",
        "",
    ]
    summary = {
        "chunks": chunk_count,
        "document_at_1": 0,
        "document_at_3": 0,
        "evidence_at_1": 0,
        "evidence_at_3": 0,
        "score": 0,
    }

    for specification in BENCHMARK_QUERIES:
        markers = EVIDENCE_MARKERS.get(specification["id"])
        if not markers:
            raise RuntimeError(f"Evidence markers are missing for {specification['id']}")
        results = store.search_with_filter(
            query=specification["query"],
            top_k=top_k,
            metadata_filter=specification["metadata_filter"],
        )
        document_rank = gold_rank(results, specification["gold_doc_ids"])
        evidence_rank = gold_evidence_rank(results, specification["gold_doc_ids"], markers)
        evidence_score = score_from_rank(evidence_rank)
        summary["document_at_1"] += document_rank == 1
        summary["document_at_3"] += document_rank is not None and document_rank <= 3
        summary["evidence_at_1"] += evidence_rank == 1
        summary["evidence_at_3"] += evidence_rank is not None and evidence_rank <= 3
        summary["score"] += evidence_score

        lines.extend(
            [
                f"QUERY {specification['id']}",
                f"query: {specification['query']}",
                f"Gold document: {', '.join(specification['gold_doc_ids'])}",
                f"Metadata filter: {specification['metadata_filter']}",
                f"Evidence markers: {markers}",
                "",
            ]
        )
        if results:
            for rank, result in enumerate(results, start=1):
                lines.extend(format_result(rank, result, markers))
        else:
            lines.extend(["No results.", ""])
        lines.extend(
            [
                f"gold_document_rank: {document_rank if document_rank is not None else 'not found'}",
                f"gold_evidence_rank: {evidence_rank if evidence_rank is not None else 'not found'}",
                f"evidence_retrieval_score: {evidence_score}",
                "",
            ]
        )

    question_count = len(BENCHMARK_QUERIES)
    lines.extend(
        [
            "SUMMARY",
            f"Document@1: {summary['document_at_1']}/{question_count}",
            f"Document@3: {summary['document_at_3']}/{question_count}",
            f"Evidence@1: {summary['evidence_at_1']}/{question_count}",
            f"Evidence@3: {summary['evidence_at_3']}/{question_count}",
            f"Evidence retrieval score: {summary['score']}/{question_count * 2}",
            "Document-level metric != final retrieval quality; evidence rank is stricter.",
            "",
        ]
    )
    return lines, summary


def parse_args() -> argparse.Namespace:
    """Build the evidence benchmark command-line interface."""
    parser = argparse.ArgumentParser(description="Benchmark chunk-level retrieval evidence.")
    parser.add_argument(
        "--chunker", choices=("fixed", "sentence", "recursive", "heading"), default="recursive"
    )
    parser.add_argument("--all-chunkers", action="store_true")
    parser.add_argument("--embedding", choices=("mock", "local", "openai", "gemini"), default="local")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("benchmark_evidence_recursive.txt"))
    return parser.parse_args()


def main() -> int:
    """Run one or all strategies and write a reproducible evidence report."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    args = parse_args()
    if args.top_k <= 0:
        print("Error: --top-k must be a positive integer.", file=sys.stderr)
        return 2

    strategies = ("fixed", "sentence", "recursive", "heading") if args.all_chunkers else (args.chunker,)
    lines: list[str] = []
    summaries: dict[str, dict[str, int]] = {}
    try:
        for strategy in strategies:
            strategy_lines, summaries[strategy] = run_strategy(strategy, args.embedding, args.top_k)
            lines.extend(strategy_lines)
        if args.all_chunkers:
            lines.extend(
                [
                    "STRATEGY COMPARISON",
                    "strategy | chunks | Document@1 | Document@3 | Evidence@1 | Evidence@3 | score/10",
                ]
            )
            for strategy in strategies:
                result = summaries[strategy]
                lines.append(
                    f"{strategy} | {result['chunks']} | {result['document_at_1']}/5 | "
                    f"{result['document_at_3']}/5 | {result['evidence_at_1']}/5 | "
                    f"{result['evidence_at_3']}/5 | {result['score']}/10"
                )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report = "\n".join(lines) + "\n"
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Evidence benchmark report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
