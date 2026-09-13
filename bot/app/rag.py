import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.metrics import RAG_QUERY_LATENCY
from app.optimization import TTLCache, normalize_query

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "matcha_knowledge")
RAG_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
RAG_CACHE = TTLCache(ttl=300)


def _qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=QDRANT_URL)


async def embed_text(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=RAG_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": OLLAMA_EMBED_MODEL, "input": text},
        )
        response.raise_for_status()
        embeddings = response.json().get("embeddings", [])

    if not embeddings:
        raise ValueError("Ollama không trả về embedding")
    return embeddings[0]


async def retrieve_context(query: str, limit: int = 4) -> str:
    normalized_query = normalize_query(query)
    cache_key = f"rag:{normalized_query}:{limit}"
    cached = RAG_CACHE.get(cache_key)
    if cached is not None:
        return cached

    client = _qdrant_client()
    try:
        if not await client.collection_exists(QDRANT_COLLECTION):
            return "Chưa có tài liệu tham khảo được nạp."

        with RAG_QUERY_LATENCY.time():
            vector = await embed_text(normalized_query)
            results = await client.query_points(
                collection_name=QDRANT_COLLECTION,
                query=vector,
                limit=limit,
                with_payload=True,
            )
        chunks = [
            point.payload.get("text", "")
            for point in results.points
            if point.payload and point.payload.get("text")
        ]
        context = "\n\n".join(chunks) or "Không tìm thấy tài liệu liên quan."
        RAG_CACHE.set(cache_key, context)
        return context
    except (httpx.HTTPError, ValueError, RuntimeError):
        return "Không truy cập được kho tài liệu."
    finally:
        await client.close()


def split_document(text: str, chunk_size: int = 900) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > chunk_size:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    source: str
    updated_at: str
    content: str


def knowledge_documents() -> list[KnowledgeDocument]:
    docs: list[KnowledgeDocument] = []
    for path in sorted(Path("knowledge").glob("*.md")):
        content = path.read_text(encoding="utf-8")
        docs.append(
            KnowledgeDocument(
                title=path.stem.replace("_", " ").title(),
                source=str(path),
                updated_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                content=content,
            )
        )
    return docs


async def ingest_documents() -> int:
    documents = knowledge_documents()
    chunks = [
        (chunk, document.title, document.source, document.updated_at)
        for document in documents
        for chunk in split_document(document.content)
    ]
    if not chunks:
        raise ValueError("Không có tài liệu trong thư mục knowledge")

    vectors = [await embed_text(chunk) for chunk, _, _, _ in chunks]
    client = _qdrant_client()
    try:
        await client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=len(vectors[0]),
                distance=models.Distance.COSINE,
            ),
        )
        await client.upsert(
            collection_name=QDRANT_COLLECTION,
            wait=True,
            points=[
                models.PointStruct(
                    id=index,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "title": title,
                        "source": source,
                        "updated_at": updated_at,
                    },
                )
                for index, ((chunk, title, source, updated_at), vector) in enumerate(zip(chunks, vectors))
            ],
        )
    finally:
        await client.close()
    return len(chunks)
