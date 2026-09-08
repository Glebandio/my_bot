import os
import logging

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]

app = FastAPI()

telegram_app = (
    Application.builder()
    .token(TOKEN)
    .updater(None)
    .build()
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")

    if update.message:
        await update.message.reply_text("Привет! 👋")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        logger.info("Получено сообщение: %s", update.message.text)

        await update.message.reply_text(
            f"Ты написал: {update.message.text}"
        )


telegram_app.add_handler(
    CommandHandler("start", start)
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        echo
    )
)


_initialized = False


async def initialize_bot():
    global _initialized

    if not _initialized:
        logger.info("Инициализация Telegram Application...")

        await telegram_app.initialize()

        _initialized = True

        logger.info("Telegram Application инициализирован")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram bot is running"
    }


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        await initialize_bot()

        data = await request.json()

        logger.info("Получен Telegram update")

        update = Update.de_json(
            data=data,
            bot=telegram_app.bot
        )

        await telegram_app.process_update(update)

        logger.info("Update обработан")

        return {
            "ok": True
        }

    except Exception:
        logger.exception("Ошибка обработки webhook")

        return {
            "ok": False
        }