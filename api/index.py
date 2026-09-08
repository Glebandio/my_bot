import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")


app = FastAPI()


telegram_app = (
    Application.builder()
    .token(TOKEN)
    .updater(None)
    .build()
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "Привет! 👋"
    )


async def echo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        f"Ты написал: {update.message.text}"
    )


telegram_app.add_handler(
    CommandHandler("start", start)
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        echo,
    )
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram bot is running",
    }


@app.post("/api/webhook")
async def webhook(request: Request):
    data = await request.json()

    update = Update.de_json(
        data=data,
        bot=telegram_app.bot,
    )

    await telegram_app.update_queue.put(update)

    return JSONResponse(
        content={"ok": True}
    )