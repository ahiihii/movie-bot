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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================
# ENV
# =========================
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8080))

if not TOKEN:
    raise ValueError("TOKEN not found!")

# =========================
# HTTP CLIENT
# =========================
client = httpx.AsyncClient(
    timeout=15,
    follow_redirects=True
)

# =========================
# MOVIE SOURCES
# =========================
SOURCES = {

    "1": {
        "name": "NguonC",
        "url": "https://phim.nguonc.com/api/films/search?keyword=",
        "base_link": "https://nguonc.com/phim/"
    },

    "2": {
        "name": "OPhim",
        "url": "https://ophim1.com/v1/api/tim-kiem?keyword=",
        "base_link": "https://ophim1.com/phim/"
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

        url = source["url"] + quote(keyword)

        response = await client.get(url)

        response.raise_for_status()

        data = response.json()

        items = (
            data.get("items")
            or data.get("data", {}).get("items")
            or []
        )

        return items[:5]

    except Exception as e:

        logger.error(f"Movie API error: {e}")

        return []

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🎬 Bot tìm phim online\n\n"
        "/1 tên phim = NguonC\n"
        "/2 tên phim = OPhim\n\n"
        "Ví dụ:\n"
        "/2 one piece"
    )

    await update.message.reply_text(text)

# =========================
# SEARCH COMMAND
# =========================
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    cmd_parts = text.split(maxsplit=1)

    if len(cmd_parts) < 2:

        await update.message.reply_text(
            "❌ Sai cú pháp.\nVí dụ:\n/2 Batman"
        )

        return

    source_id = cmd_parts[0][1:]
    keyword = cmd_parts[1]

    if source_id not in SOURCES:

        await update.message.reply_text(
            "❌ Nguồn không hợp lệ!"
        )

        return

    msg = await update.message.reply_text(
        "🔍 Đang tìm phim..."
    )

    movies = await tim_phim(source_id, keyword)

    if not movies:

        await msg.edit_text(
            "❌ Không tìm thấy phim!"
        )

        return

    keyboard = []

    for movie in movies:

        name = movie.get("name", "Unknown")
        slug = movie.get("slug", "")

        if not slug:
            continue

        callback_data = f"view|{source_id}|{slug}"

        if len(callback_data) > 60:
            continue

        keyboard.append([
            InlineKeyboardButton(
                text=name[:40],
                callback_data=callback_data
            )
        ])

    if not keyboard:

        await msg.edit_text(
            "❌ Không có dữ liệu hợp lệ!"
        )

        return

    await msg.edit_text(
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

        source = SOURCES[source_id]

        movie_link = source["base_link"] + slug

        text = (
            f"🎥 <b>{slug}</b>\n\n"
            f"🌐 Nguồn: {source['name']}\n"
            f"🔗 {movie_link}"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(f"Button handler error: {e}")

        await query.edit_message_text(
            "❌ Có lỗi xảy ra!"
        )

# =========================
# WEB SERVER
# =========================
async def health_check(request):

    return web.Response(
        text="Bot is running!"
    )

# =========================
# MAIN
# =========================
async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler(["1", "2"], search)
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern=r"^view\|"
        )
    )

    # WEB SERVER
    web_app = web.Application()

    web_app.router.add_get("/", health_check)

    runner = web.AppRunner(web_app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT
    )

    await site.start()

    # TELEGRAM BOT
    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    logger.info("Bot started successfully!")

    try:

        await asyncio.Event().wait()

    finally:

        logger.info("Shutting down...")

        await app.updater.stop()

        await app.stop()

        await app.shutdown()

        await client.aclose()

        await runner.cleanup()

# =========================
# RUN
# =========================
if __name__ == "__main__":

    asyncio.run(main())
