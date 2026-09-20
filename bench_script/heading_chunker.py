"""Section-aware chunking for Markdown and numbered policy documents."""

from __future__ import annotations

import re

from src import RecursiveChunker


class HeadingRecursiveChunker:
    """Keep section labels with chunks produced from long policy sections."""

    _MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+\S.*$")
    _NUMBERED_SECTION = re.compile(r"^\d+(?:\.\d+)*\.\s+\S.{0,140}$")

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        """Split into sections and preserve the section heading in child chunks."""
        if not text or not text.strip():
            return []

        sections = self._sections(text.strip())
        chunks: list[str] = []
        for heading, body in sections:
            section = "\n".join(part for part in (heading, body) if part).strip()
            if not section:
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            chunks.extend(self._split_section(heading, body))
        return chunks

    def _is_heading(self, line: str) -> bool:
        """Recognize explicit Markdown and numbered policy section labels only."""
        stripped = line.strip()
        return bool(
            self._MARKDOWN_HEADING.match(stripped)
            or self._NUMBERED_SECTION.match(stripped)
        )

    def _sections(self, text: str) -> list[tuple[str, str]]:
        """Return preamble and heading-led sections without treating prose as headings."""
        sections: list[tuple[str, str]] = []
        current_heading = ""
        current_body: list[str] = []
        for line in text.splitlines():
            if self._is_heading(line):
                if current_heading or current_body:
                    sections.append((current_heading, "\n".join(current_body).strip()))
                current_heading = line.strip()
                current_body = []
            else:
                current_body.append(line)
        if current_heading or current_body:
            sections.append((current_heading, "\n".join(current_body).strip()))
        return sections

    def _split_section(self, heading: str, body: str) -> list[str]:
        """Recursively split a large body while reserving room for its heading."""
        if not heading:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(body)
        if not body:
            # An unusually long heading remains intact because it is itself
            # the section context and the only permitted size exception.
            return [heading]

        prefix = f"{heading}\n"
        remaining_size = self.chunk_size - len(prefix)
        if remaining_size <= 0:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(f"{heading}\n{body}")

        body_chunks = RecursiveChunker(chunk_size=remaining_size).chunk(body)
        return [
            f"{prefix}{chunk}".strip()
            for chunk in body_chunks
            if chunk.strip()
        ]
