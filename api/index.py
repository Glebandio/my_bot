import os
import json
import logging
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from dotenv import load_dotenv

# Загружаем переменные из .env для локальной разработки
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    logger.error("BOT_TOKEN не найден!")
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

logger.info(f"Токен найден: {TOKEN[:10]}...")

# Создаем приложение
app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот-эхо.\n"
        "Просто отправь мне любое сообщение!"
    )
    logger.info(f"Пользователь {update.effective_user.id} использовал /start")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /echo"""
    text = ' '.join(context.args) if context.args else "Нет текста"
    await update.message.reply_text(f"📨 {text}")
    logger.info(f"Эхо для {update.effective_user.id}: {text}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений"""
    user_message = update.message.text
    await update.message.reply_text(f"📨 Ты написал: {user_message}")
    logger.info(f"Сообщение от {update.effective_user.id}: {user_message}")

def get_application():
    """Создает или возвращает существующее приложение"""
    global app
    if app is None:
        try:
            logger.info("Создание нового приложения...")
            app = Application.builder().token(TOKEN).build()
            
            # Регистрируем обработчики
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("echo", echo))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            logger.info("Приложение успешно создано")
        except Exception as e:
            logger.error(f"Ошибка при создании приложения: {e}")
            raise
    return app

class handler(BaseHTTPRequestHandler):
    """Обработчик запросов для Vercel"""
    
    def do_GET(self):
        """GET запрос для проверки работы"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
        logger.info("GET запрос обработан")
    
    def do_POST(self):
        """POST запрос от Telegram (вебхук)"""
        try:
            # Проверяем путь
            if self.path != '/webhook':
                self.send_response(404)
                self.end_headers()
                return
            
            # Читаем тело запроса
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                return
            
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode('utf-8'))
            
            # Логируем полученные данные
            message_text = update_data.get('message', {}).get('text', 'нет текста')
            logger.info(f"Получен вебхук: {message_text}")
            
            # Получаем приложение
            application = get_application()
            
            # Создаем update
            update = Update.de_json(update_data, application.bot)
            
            # Обрабатываем update
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(update))
            loop.close()
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
            logger.info("Вебхук успешно обработан")
            
        except Exception as e:
            logger.error(f"Ошибка в вебхуке: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())