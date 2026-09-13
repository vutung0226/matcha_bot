import os

import httpx

TELEGRAM_API = "https://api.telegram.org"


def build_webhook_url(base_url: str, path: str) -> str:
    clean_base = base_url.rstrip("/")
    clean_path = path.strip()
    if not clean_path.startswith("/"):
        clean_path = f"/{clean_path}"
    return f"{clean_base}{clean_path}"


async def set_telegram_webhook(token: str, webhook_url: str, *, drop_pending_updates: bool = True) -> dict:
    api_url = f"{TELEGRAM_API}/bot{token}/setWebhook"
    payload = {"url": webhook_url}
    if drop_pending_updates:
        payload["drop_pending_updates"] = True

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()


async def delete_telegram_webhook(token: str) -> dict:
    api_url = f"{TELEGRAM_API}/bot{token}/deleteWebhook"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(api_url, json={"drop_pending_updates": True})
        response.raise_for_status()
        return response.json()


def webhook_from_env() -> str:
    base_url = os.getenv("WEBHOOK_URL", "").strip()
    path = os.getenv("WEBHOOK_PATH", "/telegram").strip()
    if not base_url:
        raise RuntimeError("WEBHOOK_URL chưa được cấu hình")
    return build_webhook_url(base_url, path)
