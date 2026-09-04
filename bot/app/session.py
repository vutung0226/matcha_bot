import json
import logging
import os

from redis.asyncio import Redis

logger = logging.getLogger(__name__)
VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))
SESSION_MAX_TURNS = int(os.getenv("SESSION_MAX_TURNS", "10"))


def _session_key(chat_id: str) -> str:
    return f"matcha:session:{chat_id}"


async def _redis() -> Redis:
    client = Redis.from_url(VALKEY_URL, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        await client.aclose()
        raise
    return client


async def get_history(chat_id: str) -> list[dict[str, str]]:
    client = None
    try:
        client = await _redis()
        values = await client.lrange(_session_key(chat_id), -SESSION_MAX_TURNS * 2, -1)
        return [json.loads(value) for value in values]
    except Exception as error:
        logger.warning("Không đọc được session từ Valkey: %s", error)
        return []
    finally:
        if client:
            await client.aclose()


async def save_exchange(chat_id: str, user_message: str, assistant_reply: str) -> None:
    client = None
    try:
        client = await _redis()
        key = _session_key(chat_id)
        await client.rpush(
            key,
            json.dumps({"role": "user", "content": user_message}, ensure_ascii=False),
            json.dumps({"role": "assistant", "content": assistant_reply}, ensure_ascii=False),
        )
        await client.ltrim(key, -SESSION_MAX_TURNS * 2, -1)
        await client.expire(key, SESSION_TTL)
    except Exception as error:
        logger.warning("Không lưu được session vào Valkey: %s", error)
    finally:
        if client:
            await client.aclose()


async def clear_session(chat_id: str) -> None:
    client = None
    try:
        client = await _redis()
        await client.delete(_session_key(chat_id))
    except Exception as error:
        logger.warning("Không xóa được session từ Valkey: %s", error)
    finally:
        if client:
            await client.aclose()
