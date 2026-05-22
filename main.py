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
    raise ValueError("TOKEN environment variable not found!")

# =========================
# HTTP CLIENT
# =========================
client = httpx.AsyncClient(timeout=15)

# =========================
# MOVIE SOURCES
# =========================
SOURCES = {
    '1': {
        'name': 'NguonC',
        'url': 'https://phim.nguonc.com/api/films/search?keyword=',
        'base_link': 'https://nguonc.com/phim/'
    },

    '2': {
        'name': 'OPhim',
        'url': 'https://ophim1.com/v1/api/tim-kiem?keyword=',
        'base_link': 'https://ophim.cc/phim/'
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

        logger.info(f"API response: {data}")

        items = (
            data.get('items')
            or data.get('data', {}).get('items')
            or []
        )

        return items[:5]

    except Exception as e:
        logger.error(f"Movie API error: {e}")
        return None

# =========================
# SEARCH COMMAND
# =========================
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    cmd_parts = text.split(maxsplit=1)

    if len(cmd_parts) < 2:
        await update.message.reply_text(
            "📌 Cú pháp:\n\n"
            "/1 tên phim\n"
            "/2 tên phim"
        )
        return

    source_id = cmd_parts[0][1:]
    keyword = cmd_parts[1]

    msg = await update.message.reply_text("🔍 Đang tìm phim...")

    movies = await tim_phim(source_id, keyword)

    if not movies:
        await msg.edit_text("❌ Không tìm thấy phim!")
        return

    # =========================
    # BUTTONS
    # =========================
    keyboard = []

    for movie in movies:

        movie_name = movie.get("name", "Unknown")

        callback_data = (
            f"view|{source_id}|{movie.get('slug', '')}"
        )

        keyboard.append([
            InlineKeyboardButton(
                movie_name,
                callback_data=callback_data
            )
        ])

    # =========================
    # FIRST MOVIE INFO
    # =========================
    first_movie = movies[0]

    poster = (
        first_movie.get("thumb_url")
        or first_movie.get("poster_url")
    )

    # Fix relative image url
    if poster and poster.startswith("/"):
        poster = "https://phimimg.com/" + poster

    name = first_movie.get("name", "Không tên")
    origin = first_movie.get("origin_name", "")
    year = first_movie.get("year", "")

    caption = (
        f"🎬 <b>{name}</b>\n"
        f"🌍 {origin}\n"
        f"📅 {year}\n\n"
        f"👇 Chọn phim bên dưới:"
    )

    # =========================
    # SEND POSTER
    # =========================
    try:

        if poster:

            await update.message.reply_photo(
                photo=poster,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        else:

            await update.message.reply_text(
                caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        await msg.delete()

    except Exception as e:

        logger.error(f"Poster send error: {e}")

        await update.message.reply_text(
            caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =========================
# BUTTON HANDLER
# =========================
async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    try:

        _, source_id, slug = query.data.split("|")

        source = SOURCES.get(source_id)

        movie_link = f"{source['base_link']}{slug}"

        text = (
            f"🎥 <b>Thông tin phim</b>\n\n"
            f"🌍 Nguồn: {source['name']}\n"
            f"🔗 <a href='{movie_link}'>Xem phim tại đây</a>"
        )

        await query.edit_message_caption(
            caption=text,
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(f"Button error: {e}")

        try:
            await query.edit_message_text(
                "❌ Có lỗi xảy ra!"
            )
        except:
            pass

# =========================
# WEB SERVER
# =========================
async def home(request):
    return web.Response(text="Bot is running!")

# =========================
# MAIN
# =========================
async def main():

    # Telegram App
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(['1', '2'], search)
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
        '0.0.0.0',
        PORT
    )

    await site.start()

    # Telegram start
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logger.info("Bot started successfully!")

    # Keep alive
    while True:
        await asyncio.sleep(3600)

# =========================
# START
# =========================
if __name__ == '__main__':
    asyncio.run(main())
