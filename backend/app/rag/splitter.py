from dataclasses import dataclass
from hashlib import sha256

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
RELATED_TOPIC_GROUPS = {
    "Gaming": "Gaming and thermals",
    "Thermals": "Gaming and thermals",
    "Camera": "Camera and video",
    "Video": "Camera and video",
    "Strengths": "Strengths and weaknesses",
    "Weaknesses": "Strengths and weaknesses",
}


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    source_name: str
    chunk_index: int
    topic: str | None
    content: str
    embedding_text: str
    content_hash: str
    metadata: dict[str, str]


def split_markdown_document(
    markdown_text: str,
    *,
    source_name: str,
    product_name: str,
) -> list[KnowledgeChunk]:
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "product"),
            ("##", "topic"),
            ("###", "subtopic"),
        ],
        strip_headers=False,
    )
    sections = markdown_splitter.split_text(markdown_text)
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    grouped_sections: dict[str, list[Document]] = {}
    group_metadata: dict[str, dict[str, str]] = {}
    for section in sections:
        topic = str(section.metadata.get("topic") or "General")
        group = RELATED_TOPIC_GROUPS.get(topic, topic)
        grouped_sections.setdefault(group, []).append(section)
        group_metadata.setdefault(group, {}).update(
            {
                key: str(value)
                for key, value in section.metadata.items()
                if value is not None
            }
        )

    chunks: list[KnowledgeChunk] = []
    for group, grouped in grouped_sections.items():
        grouped_content = "\n\n".join(
            section.page_content.strip() for section in grouped if section.page_content.strip()
        )
        if not grouped_content:
            continue

        metadata = {**group_metadata[group], "topic": group}
        documents = recursive_splitter.split_documents(
            [Document(page_content=grouped_content, metadata=metadata)]
        )
        for document in documents:
            raw_content = document.page_content.strip()
            if not raw_content:
                continue
            metadata = {
                key: str(value)
                for key, value in document.metadata.items()
                if value is not None
            }
            topic = metadata.get("topic") or metadata.get("subtopic")
            context = [f"Product: {product_name}"]
            if topic:
                context.append(f"Topic: {topic}")
            if metadata.get("subtopic"):
                context.append(f"Subtopic: {metadata['subtopic']}")
            embedding_text = "\n".join(context) + f"\n\n{raw_content}"
            chunks.append(
                KnowledgeChunk(
                    source_name=source_name,
                    chunk_index=len(chunks),
                    topic=topic,
                    content=raw_content,
                    embedding_text=embedding_text,
                    content_hash=sha256(raw_content.encode("utf-8")).hexdigest(),
                    metadata={
                        "product": product_name,
                        "source_name": source_name,
                        **metadata,
                    },
                )
            )

    if not chunks:
        raise ValueError(f"Knowledge document {source_name} produced no chunks")
    return chunks
