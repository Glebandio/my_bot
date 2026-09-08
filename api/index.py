import os
import json
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

# Создаем приложение
app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-эхо.\n"
        "Просто отправь мне любое сообщение!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текст сообщения
    text = update.message.text
    
    # Проверяем, есть ли текст после команды /echo
    if context.args:
        text = ' '.join(context.args)
    
    # Отправляем обратно
    await update.message.reply_text(f"📨 {text}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Просто повторяем сообщение пользователя
    user_message = update.message.text
    await update.message.reply_text(f"📨 Ты написал: {user_message}")

def get_application():
    global app
    if app is None:
        app = Application.builder().token(TOKEN).build()
        
        # Регистрируем команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("echo", echo))
        
        # Обработчик всех текстовых сообщений
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return app

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook':
            try:
                # Читаем данные
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                update_data = json.loads(body.decode('utf-8'))
                
                # Получаем приложение
                application = get_application()
                
                # Создаем update
                update = Update.de_json(update_data, application.bot)
                
                # Обрабатываем
                asyncio.run(application.process_update(update))
                
                # Ответ
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_GET(self):
        # Просто для проверки что бот работает
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')