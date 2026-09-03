import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.handlers import help_command, message_handler, start_command

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
    application = build_application()
    logger.info("Bot đang chạy ở chế độ polling...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
