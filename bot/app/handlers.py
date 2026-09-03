import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


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
    """Placeholder cho phần trả lời thông minh.

    TODO: thay bằng lời gọi RAG + LLM (Groq API hoặc Ollama local) theo thiết kế
    trong design-opensource.md (mục 1b). Hiện tại chỉ echo lại để xác nhận bot
    đã chạy được end-to-end trước khi tích hợp AI.
    """
    return f"Mình đã nhận câu hỏi: \"{user_message}\"\n(Phần trả lời AI sẽ được tích hợp ở bước tiếp theo.)"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    logger.info("Nhận tin nhắn từ %s: %s", update.effective_user.id, user_message)

    reply = await generate_reply(user_message)
    await update.message.reply_text(reply)
