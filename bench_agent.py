"""Benchmark grounded KnowledgeBaseAgent answers with a real generation LLM."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from bench import (
    BENCHMARK_QUERIES,
    EVIDENCE_MARKERS,
    build_store,
    create_chunker,
    create_embedder,
    gold_evidence_rank,
    load_source_documents,
    normalise_text,
    preview,
)
from src.agent import KnowledgeBaseAgent


def create_openai_llm() -> tuple[Callable[[str], str], str]:
    """Create an OpenAI generation callback without falling back to a mock."""
    load_dotenv(override=False)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for --llm openai.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK is unavailable. Install: python -m pip install openai") from exc

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    client = OpenAI()

    def generate(prompt: str) -> str:
        """Generate one grounded answer from the supplied agent prompt."""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    return generate, model


def format_retrieved_evidence(results: list[dict[str, Any]]) -> list[str]:
    """Render the same top-three evidence supplied to the agent retrieval path."""
    if not results:
        return ["No results.", ""]
    lines: list[str] = []
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        lines.extend(
            [
                f"TOP {rank}",
                f"doc_id: {metadata.get('doc_id', '')}",
                f"platform: {metadata.get('platform', '')}",
                f"score: {result['score']:.6f}",
                f"content preview: {preview(result['content'])}",
                "",
            ]
        )
    return lines


def evaluate_answer(
    answer: str, results: list[dict[str, Any]], specification: dict[str, Any]
) -> tuple[str, list[str], list[str]]:
    """Evaluate required source concepts with transparent exact marker checks."""
    markers = EVIDENCE_MARKERS[specification["id"]]
    answer_text = normalise_text(answer)
    matched = [marker for marker in markers if normalise_text(marker) in answer_text]
    missing = [marker for marker in markers if marker not in matched]
    retrieved_evidence = gold_evidence_rank(
        results, specification["gold_doc_ids"], markers
    )
    if retrieved_evidence is None:
        verdict = "incorrect"
    elif not missing:
        verdict = "correct"
    else:
        verdict = "partial"
    return verdict, matched, missing


def run_benchmark(args: argparse.Namespace) -> list[str]:
    """Run heading retrieval and evaluate one real LLM answer for every query."""
    llm_fn, model = create_openai_llm()
    documents = load_source_documents()
    chunker, chunker_parameters = create_chunker("heading")
    store, chunk_count = build_store(documents, chunker, create_embedder("local"))
    agent = KnowledgeBaseAgent(store, llm_fn)
    lines = [
        "KNOWLEDGE BASE AGENT BENCHMARK",
        "embedding backend: local",
        "chunker: heading",
        f"chunker parameters: {chunker_parameters}",
        f"generation backend: openai ({model})",
        f"source documents: {len(documents)}",
        f"chunks: {chunk_count}",
        "top_k: 3",
        "",
    ]

    correct = 0
    partial = 0
    incorrect = 0
    for specification in BENCHMARK_QUERIES:
        results = store.search_with_filter(
            specification["query"], top_k=3, metadata_filter=specification["metadata_filter"]
        )
        answer = agent.answer(
            specification["query"], top_k=3, metadata_filter=specification["metadata_filter"]
        )
        verdict, matched, missing = evaluate_answer(answer, results, specification)
        if verdict == "correct":
            correct += 1
        elif verdict == "partial":
            partial += 1
        else:
            incorrect += 1
        lines.extend(
            [
                f"QUERY {specification['id']}",
                "",
                f"Question:\n{specification['query']}",
                "",
                f"Gold answer:\n{specification['gold_answer']}",
                "",
                f"Metadata filter:\n{specification['metadata_filter']}",
                "",
                "Retrieved evidence:",
            ]
        )
        lines.extend(format_retrieved_evidence(results))
        lines.extend(
            [
                f"Agent answer:\n{answer}",
                "",
                "Evaluation:",
                f"required evidence concepts: {markers_to_text(EVIDENCE_MARKERS[specification['id']])}",
                f"matched concepts: {markers_to_text(matched)}",
                f"missing concepts: {markers_to_text(missing)}",
                f"retrieved complete evidence: {gold_evidence_rank(results, specification['gold_doc_ids'], EVIDENCE_MARKERS[specification['id']]) is not None}",
                f"verdict: {verdict}",
                "",
            ]
        )
    lines.extend(
        [
            "SUMMARY",
            f"correct: {correct}/{len(BENCHMARK_QUERIES)}",
            f"partial: {partial}/{len(BENCHMARK_QUERIES)}",
            f"incorrect: {incorrect}/{len(BENCHMARK_QUERIES)}",
            "Evaluation uses deterministic source-evidence markers, not LLM self-scoring.",
        ]
    )
    return lines


def markers_to_text(markers: list[str]) -> str:
    """Render a marker list without making an empty list ambiguous."""
    return ", ".join(markers) if markers else "none"


def parse_args() -> argparse.Namespace:
    """Build the command-line interface for real-LLM agent evaluation."""
    parser = argparse.ArgumentParser(description="Benchmark KnowledgeBaseAgent answers.")
    parser.add_argument("--llm", choices=("openai",), default="openai")
    parser.add_argument("--output", type=Path, default=Path("agent_benchmark_results.txt"))
    return parser.parse_args()


def main() -> int:
    """Write a report only after a full real-LLM benchmark completes."""
    args = parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    try:
        lines = run_benchmark(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    report = "\n".join(lines) + "\n"
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Agent benchmark report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
