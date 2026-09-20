from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if metadata_filter:
            results = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        else:
            results = self.store.search(question, top_k=top_k)
        context_blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            label_parts = [f"{index}"]
            for key in ("title", "doc_id", "source_url"):
                if metadata.get(key):
                    label_parts.append(f"{key}={metadata[key]}")
            context_blocks.append(f"[{'; '.join(label_parts)}] {result['content']}")

        context = "\n\n".join(context_blocks) or "No relevant context was retrieved."
        prompt = (
            "You are a knowledge-base assistant.\n\n"
            "Use only the supplied context.\n"
            "If the context does not contain enough information, say so.\n"
            "Do not invent facts.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}"
        )
        return str(self.llm_fn(prompt))
