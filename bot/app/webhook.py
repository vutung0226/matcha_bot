import os

from fastapi import FastAPI, Request
from telegram import Update

from app.config import BOT_TOKEN
from app.handlers import help_command, message_handler, start_command
from app.main import build_application


def create_webhook_app() -> FastAPI:
    app = FastAPI(title="Matcha Telegram Bot Webhook")
    application = build_application()

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "matcha-bot"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/telegram")
    async def telegram_webhook(request: Request) -> dict[str, bool]:
        payload = await request.json()
        update = Update.de_json(payload, application.bot)
        if update is not None:
            await application.process_update(update)
        return {"ok": True}

    return app
