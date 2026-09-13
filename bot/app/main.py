import logging
import os

from prometheus_client import start_http_server
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.handlers import help_command, message_handler, start_command
from app.webhook_setup import webhook_from_env

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "false").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8001"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return application


def main() -> None:
    start_http_server(8000)
    application = build_application()

    if WEBHOOK_MODE:
        if not WEBHOOK_URL:
            raise RuntimeError("WEBHOOK_URL chưa được cấu hình khi WEBHOOK_MODE=true")
        webhook_url = webhook_from_env()
        logger.info("Bot đang chạy ở chế độ webhook: %s", webhook_url)
        application.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path=WEBHOOK_PATH.lstrip("/"),
            webhook_url=webhook_url,
        )
        return

    logger.info("Bot đang chạy ở chế độ polling...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
