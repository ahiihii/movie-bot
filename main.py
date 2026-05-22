import os
import logging
import asyncio
import httpx

from aiohttp import web
from urllib.parse import quote

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================
# ENV
# =========================

TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    raise ValueError("TOKEN environment variable not found!")

# =========================
# HTTP CLIENT
# =========================

client = httpx.AsyncClient(timeout=10)

# =========================
# SOURCES
# =========================

SOURCES = {
    '1': {
        'url': 'https://api.nguonc.com/api/films/search?keyword=',
        'base_link': 'https://nguonc.com/phim/'
    },
    '2': {
        'url': 'https://api.kkphim.com/api/films/search?keyword=',
        'base_link': 'https://kkphim.com/phim/'
    },
    '3': {
        'url': 'https://ophim1.com/v1/api/tim-kiem?keyword=',
        'base_link': 'https://ophim1.com/phim/'
    }
}

# =========================
# SEARCH MOVIE
# =========================

async def tim_phim(source_id, keyword):

    source = SOURCES.get(source_id)

    if not source:
        return None

    try:

        url = source['url'] + quote(keyword)

        response = await client.get(url)

        response.raise_for_status()

        data = response.json()

        items = (
            data.get('data', {}).get('items')
            or data.get('items')
            or []
        )

        return items[:5]

    except Exception as e:

        logger.error(f"Movie API error: {e}")

        return None

# =========================
# COMMAND HANDLER
# =========================

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    cmd_parts = text.split(maxsplit=1)

    if len(cmd_parts) < 2:

        await update.message.reply_text(
            "Cú pháp:\n/1 Batman"
        )

        return

    source_id = cmd_parts[0][1:]

    keyword = cmd_parts[1]

    await update.message.reply_text("🔍 Đang tìm phim...")

    movies = await tim_phim(source_id, keyword)

    if not movies:

        await update.message.reply_text(
            "❌ Không tìm thấy phim!"
        )

        return

    keyboard = []

    for movie in movies:

        name = movie.get("name", "Unknown")

        slug = movie.get("slug", "")

        callback_data = f"view|{source_id}|{slug}"

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=callback_data
            )
        ])

    await update.message.reply_text(
        "🎬 Chọn phim:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    try:

        _, source_id, slug = query.data.split("|")

        await query.edit_message_text(
            f"🎥 Bạn đã chọn:\n\nNguồn: {source_id}\nSlug: {slug}"
        )

    except Exception as e:

        logger.error(f"Button error: {e}")

        await query.edit_message_text(
            "❌ Có lỗi xảy ra!"
        )

# =========================
# WEB SERVER
# =========================

async def home(request):

    return web.Response(
        text="Bot is running!"
    )

# =========================
# MAIN
# =========================

async def main():

    # Telegram app
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(['1', '2', '3'], search)
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern=r"^view\|"
        )
    )

    # Web server
    web_app = web.Application()

    web_app.router.add_get('/', home)

    runner = web.AppRunner(web_app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        host='0.0.0.0',
        port=PORT
    )

    await site.start()

    logger.info(f"Web server running on port {PORT}")

    # Telegram lifecycle MANUAL
    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    logger.info("Bot started successfully!")

    # giữ process sống mãi
    while True:
        await asyncio.sleep(3600)

# =========================
# RUN
# =========================

if __name__ == '__main__':

    asyncio.run(main())
