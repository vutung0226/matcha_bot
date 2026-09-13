import os

import uvicorn

from app.webhook import create_webhook_app


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(create_webhook_app(), host=host, port=port)
