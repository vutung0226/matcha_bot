from prometheus_client import Counter, Histogram, start_http_server

LLM_REQUESTS_TOTAL = Counter(
    "telegram_bot_llm_requests_total",
    "Total number of LLM requests handled by the Telegram bot",
    labelnames=("model", "status"),
)

LLM_LATENCY_SECONDS = Histogram(
    "telegram_bot_llm_latency_seconds",
    "Time spent waiting for the local Ollama model response",
    labelnames=("model",),
    buckets=(0.25, 0.5, 1, 2, 5, 10, 20, 40, 60),
)

RAG_QUERY_LATENCY = Histogram(
    "telegram_bot_rag_query_latency_seconds",
    "Time spent retrieving relevant context from Qdrant",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

__all__ = [
    "LLM_REQUESTS_TOTAL",
    "LLM_LATENCY_SECONDS",
    "RAG_QUERY_LATENCY",
    "start_http_server",
]
