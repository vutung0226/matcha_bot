import asyncio
import logging

from app.rag import ingest_documents

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    chunk_count = await ingest_documents()
    logging.info("Đã nạp %s đoạn tài liệu vào Qdrant", chunk_count)


if __name__ == "__main__":
    asyncio.run(main())
