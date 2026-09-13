import logging
import os
import time

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.metrics import LLM_LATENCY_SECONDS, LLM_REQUESTS_TOTAL
from app.optimization import normalize_query
from app.rag import retrieve_context
from app.session import clear_session, get_history, save_exchange

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        await clear_session(str(update.effective_chat.id))
    await update.message.reply_text(
        "Xin chào! Mình là trợ lý tư vấn Matcha 🍵\n"
        "Gõ câu hỏi bất kỳ về Matcha (nguồn gốc, cách pha, nhiệt độ nước...) mình sẽ trả lời.\n"
        "Dùng /help để xem hướng dẫn."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Các lệnh hỗ trợ:\n"
        "/start - Bắt đầu trò chuyện\n"
        "/help - Xem hướng dẫn\n\n"
        "Hoặc chỉ cần gõ câu hỏi về Matcha, ví dụ: 'Nhiệt độ nước pha matcha bao nhiêu là chuẩn?'"
    )


async def generate_reply(user_message: str, chat_id: str | None = None) -> str:
    normalized_message = normalize_query(user_message)
    context = await retrieve_context(normalized_message)
    history = await get_history(chat_id) if chat_id else []
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý tư vấn matcha bằng tiếng Việt. "
                    "Trả lời chính xác, thân thiện, ngắn gọn. "
                    "Nếu không chắc hoặc tài liệu không có thông tin, hãy nói rõ thay vì bịa thông tin. "
                    "Chỉ sử dụng thông tin trong phần TÀI LIỆU THAM KHẢO khi câu hỏi liên quan đến kiến thức matcha."
                ),
            },
            *history,
            {"role": "user", "content": f"TÀI LIỆU THAM KHẢO:\n{context}\n\nCÂU HỎI:\n{normalized_message}"},
        ],
        "options": {"temperature": 0.4},
    }

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            reply = response.json().get("message", {}).get("content", "").strip()
        LLM_REQUESTS_TOTAL.labels(model=OLLAMA_MODEL, status="success").inc()
        LLM_LATENCY_SECONDS.labels(model=OLLAMA_MODEL).observe(time.perf_counter() - start)
    except (httpx.HTTPError, ValueError) as error:
        logger.exception("Không thể gọi Ollama: %s", error)
        LLM_REQUESTS_TOTAL.labels(model=OLLAMA_MODEL, status="error").inc()
        LLM_LATENCY_SECONDS.labels(model=OLLAMA_MODEL).observe(time.perf_counter() - start)
        return (
            "Mình chưa kết nối được với model AI local. "
            "Hãy kiểm tra Ollama và model đã được khởi động chưa."
        )

    reply = reply or "Model chưa trả về nội dung. Bạn thử hỏi lại nhé."
    if chat_id:
        await save_exchange(chat_id, user_message, reply)
    return reply


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    logger.info("Nhận tin nhắn từ %s: %s", update.effective_user.id, user_message)

    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    reply = await generate_reply(user_message, chat_id)
    await update.message.reply_text(reply)
