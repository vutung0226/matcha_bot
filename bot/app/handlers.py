import logging
import os

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.rag import retrieve_context

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def generate_reply(user_message: str) -> str:
    context = await retrieve_context(user_message)
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
            {
                "role": "user",
                "content": f"TÀI LIỆU THAM KHẢO:\n{context}\n\nCÂU HỎI:\n{user_message}",
            },
        ],
        "options": {"temperature": 0.4},
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            reply = response.json().get("message", {}).get("content", "").strip()
    except (httpx.HTTPError, ValueError) as error:
        logger.exception("Không thể gọi Ollama: %s", error)
        return (
            "Mình chưa kết nối được với model AI local. "
            "Hãy kiểm tra Ollama và model đã được khởi động chưa."
        )

    return reply or "Model chưa trả về nội dung. Bạn thử hỏi lại nhé."


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    logger.info("Nhận tin nhắn từ %s: %s", update.effective_user.id, user_message)

    reply = await generate_reply(user_message)
    await update.message.reply_text(reply)
