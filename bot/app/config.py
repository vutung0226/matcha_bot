import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN chưa được cấu hình. Tạo file .env từ .env.example và điền token lấy từ @BotFather."
    )
