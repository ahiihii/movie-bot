import os
import logging
import asyncio
import httpx

from aiohttp import web
from urllib.parse import quote

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
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
    raise ValueError("TOKEN not found!")

# =========================
# HTTP CLIENT
# =========================
client = httpx.AsyncClient(timeout=15)

# =========================
# SOURCES
# =========================
SOURCES = {
  SOURCES = {
    '1': {
        'url': 'https://phim.nguonc.com/api/films/search?keyword=',
        'base_link': 'https://nguonc.com/phim/'
    },
    '2': {
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
        return []

    try:
        url = source['url'] + quote(keyword)

        logger.info(f"Searching: {url}")

        response = await client.get(url)
        response.raise_for_status()

        data = response.json()

        logger.info(data)

        # Hỗ trợ nhiều kiểu JSON
        items = (
            data.get("items")
            or data.get("data", {}).get("items")
            or []
        )

        return items[:5]

    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

# =========================
# COMMAND SEARCH
# =========================
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        text = update.message.text.strip()

        parts = text.split(maxsplit=1)

        if len(parts) < 2:
            await update.message.reply_text(
                "📌 Cú pháp:\n"
                "/1 tên phim\n"
                "/2 tên phim"
            )
            return

        source_id = parts[0][1:]
        keyword = parts[1]

        loading = await update.message.reply_text(
            "🔍 Đang tìm phim..."
        )

        movies = await tim_phim(source_id, keyword)

        if not movies:
            await loading.edit_text("❌ Không tìm thấy phim!")
            return

        keyboard = []

        for movie in movies:

            name = movie.get("name", "Không tên")
            slug = movie.get("slug", "")

            keyboard.append([
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"movie|{source_id}|{slug}"
                )
            ])

        await loading.edit_text(
            "🎬 Chọn phim:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Search handler error: {e}")

        await update.message.reply_text(
            "❌ Có lỗi xảy ra!"
        )

# =========================
# BUTTON HANDLER
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    try:
        _, source_id, slug = query.data.split("|")

        source = SOURCES[source_id]

        movie_url = source['base_link'] + slug

        # Lấy dữ liệu lại để tìm đúng phim
        api_url = source['url'] + quote(slug)

        response = await client.get(api_url)

        data = response.json()

        items = (
            data.get("items")
            or data.get("data", {}).get("items")
            or []
        )

        movie = None

        for item in items:
            if item.get("slug") == slug:
                movie = item
                break

        if not movie:
            await query.edit_message_text("❌ Không lấy được thông tin phim!")
            return

        name = movie.get("name", "Không tên")

        poster = (
            movie.get("thumb_url")
            or movie.get("poster_url")
        )

        # Fix ảnh relative path
        if poster and poster.startswith("/"):
            poster = "https://phimimg.com/" + poster.lstrip("/")

        caption = (
            f"🎬 {name}\n\n"
            f"🌐 Nguồn: {source['name']}\n"
            f"🔗 {movie_url}"
        )

        if poster:

            try:
                await query.message.reply_photo(
                    photo=poster,
                    caption=caption
                )

            except Exception as e:
                logger.error(f"Photo error: {e}")

                await query.message.reply_text(caption)

        else:
            await query.message.reply_text(caption)

    except Exception as e:

        logger.error(f"Button handler error: {e}")

        await query.edit_message_text(
            "❌ Có lỗi xảy ra!"
        )

# =========================
# WEB SERVER
# =========================
async def home(request):
    return web.Response(text="Bot is running!")

# =========================
# MAIN
# =========================
async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler(['1', '2'], search))

    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern=r"^movie\|"
        )
    )

    # Web server cho Render
    web_app = web.Application()

    web_app.router.add_get("/", home)

    runner = web.AppRunner(web_app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    logger.info(f"Web server running on port {PORT}")

    # Start bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logger.info("Bot started!")

    while True:
        await asyncio.sleep(3600)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(main())
