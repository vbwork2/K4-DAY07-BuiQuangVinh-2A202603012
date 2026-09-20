from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import LocalEmbedder, MockEmbedder, compute_similarity

PAIRS = [
    {
        "id": 1,
        "a": "Người mua có thể trả hàng trong vòng 15 ngày.",
        "b": "Khách hàng được phép hoàn trả sản phẩm trong thời hạn 15 ngày.",
        "prediction": "cao",
    },
    {
        "id": 2,
        "a": "Người bán phải phản hồi yêu cầu hoàn tiền.",
        "b": "Seller cần phản hồi tranh chấp của khách hàng.",
        "prediction": "cao",
    },
    {
        "id": 3,
        "a": "Sản phẩm bị lỗi có thể được hoàn tiền.",
        "b": "Hàng hư hỏng có thể đủ điều kiện trả lại.",
        "prediction": "cao",
    },
    {
        "id": 4,
        "a": "Người mua yêu cầu hoàn tiền.",
        "b": "Người bán cập nhật tồn kho.",
        "prediction": "thấp",
    },
    {
        "id": 5,
        "a": "TikTok xử lý tranh chấp hậu mãi.",
        "b": "Shopee quy định phí vận chuyển trả hàng.",
        "prediction": "thấp",
    },
]


def create_embedder(name: str):
    if name == "mock":
        return MockEmbedder()
    try:
        return LocalEmbedder()
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "Local embeddings are unavailable. Install:\n"
            "python -m pip install -r requirements-local.txt"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Could not initialize local embeddings: {exc}") from exc


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Evaluate 5 similarity prediction pairs.")
    parser.add_argument("--embedding", choices=("local", "mock"), default="local")
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--output", type=Path, default=Path("similarity_results.txt"))
    args = parser.parse_args()

    try:
        embedder = create_embedder(args.embedding)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    lines = [
        "Similarity prediction experiment",
        f"embedding: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}",
        f"decision threshold: {args.threshold:.2f}",
        "",
        "id | prediction | score | actual_label | correct | sentence_a | sentence_b",
    ]

    correct_count = 0
    for pair in PAIRS:
        vec_a = embedder(pair["a"])
        vec_b = embedder(pair["b"])
        score = compute_similarity(vec_a, vec_b)
        actual = "cao" if score >= args.threshold else "thấp"
        correct = actual == pair["prediction"]
        correct_count += int(correct)

        lines.append(
            f'{pair["id"]} | {pair["prediction"]} | {score:.6f} | {actual} | '
            f'{"yes" if correct else "no"} | {pair["a"]} | {pair["b"]}'
        )

    lines.extend(
        [
            "",
            f"correct_predictions: {correct_count}/{len(PAIRS)}",
            "",
            "NOTE:",
            "- Prediction is written before looking at the score.",
            "- The threshold is an experiment convention, not a universal semantic-similarity law.",
            "- Prefer --embedding local for the report; mock embeddings do not model semantic meaning.",
        ]
    )

    report = "\n".join(lines) + "\n"
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
