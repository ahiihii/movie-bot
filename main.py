import os
import logging
import httpx
import asyncio
from aiohttp import web
from urllib.parse import quote
from html import escape
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging và Token
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8080)) # Render sẽ cấp PORT này

# Global Session
client = httpx.AsyncClient(timeout=10)

# Phần logic bot (giữ nguyên như cũ)
SOURCES = {
    '1': {'url': 'https://api.nguonc.com/api/films/search?keyword=', 'base_link': 'https://nguonc.com/phim/'},
    '2': {'url': 'https://api.kkphim.com/api/films/search?keyword=', 'base_link': 'https://kkphim.com/phim/'},
    '3': {'url': 'https://ophim1.com/v1/api/tim-kiem?keyword=', 'base_link': 'https://ophim1.com/phim/'}
}

async def tim_phim(source_id, keyword):
    source = SOURCES.get(source_id)
    if not source: return None
    try:
        res = await client.get(source['url'] + quote(keyword))
        res.raise_for_status()
        data = res.json()
        return (data.get('data', {}).get('items') or data.get('items') or [])[:5]
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd_parts = update.message.text.split(maxsplit=1)
    if len(cmd_parts) < 2:
        await update.message.reply_text("Cú pháp: /<nguồn> [tên phim]")
        return
    source_id = cmd_parts[0][1:]
    movies = await tim_phim(source_id, cmd_parts[1])
    if not movies:
        await update.message.reply_text("Không tìm thấy kết quả!")
        return
    keyboard = [[InlineKeyboardButton(m.get('name'), callback_data=f"view|{source_id}|{m.get('slug')}")] for m in movies]
    await update.message.reply_text("Chọn phim:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Đang lấy chi tiết...")

# --- THÊM PHẦN NÀY ĐỂ CHẠY TRÊN WEB SERVICE ---
async def web_server(request):
    return web.Response(text="Bot is running!")

if __name__ == '__main__':
    # 1. Khởi tạo bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(['1', '2', '3'], search))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # 2. Chạy web server song song
    web_app = web.Application()
    web_app.add_routes([web.get('/', web_server)])
    runner = web.AppRunner(web_app)
    
    async def run_both():
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        logger.info(f"Bot & Web Server running on port {PORT}")
        await app.run_polling()

    asyncio.run(run_both())
