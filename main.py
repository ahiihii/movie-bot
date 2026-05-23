from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)

import httpx
import os
import asyncio

# =====================================================
# RENDER ANTI SLEEP
# =====================================================

from flask import Flask
from threading import Thread

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():

    port = int(
        os.environ.get("PORT", 10000)
    )

    web.run(
        host="0.0.0.0",
        port=port
    )

Thread(
    target=run_web,
    daemon=True
).start()

# =====================================================
# TOKEN
# =====================================================

TOKEN = os.getenv("BOT_TOKEN")

print("TOKEN =", TOKEN)

# =====================================================
# SOURCES
# =====================================================

SOURCES = {

    "1": {
        "name": "NGUONC",
        "tag": "Vietsub",
        "search": "https://phim.nguonc.com/api/films/search?keyword=",
        "detail": "https://phim.nguonc.com/api/film/",
    },

    "2": {
        "name": "OPHIM",
        "tag": "Vietsub + Thuyết Minh",
        "search": "https://ophim1.com/v1/api/tim-kiem?keyword=",
        "detail": "https://ophim1.com/phim/",
    },

    "3": {
        "name": "KKPHIM",
        "tag": "Vietsub + Lồng Tiếng",
        "search": "https://phimapi.com/v1/api/tim-kiem?keyword=",
        "detail": "https://phimapi.com/phim/",
    }
}

# =====================================================
# HTTP CLIENT
# =====================================================

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}

client = httpx.AsyncClient(
    timeout=30,
    headers=headers,
    follow_redirects=True
)

# =====================================================
# START
# =====================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🎬 CHÀO MỪNG ĐẾN VỚI BOT XEM PHIM\n\n"

        "🔎 Chỉ cần gửi tên phim vào chat\n\n"

        "📌 Ví dụ:\n"
        "• one piece\n"
        "• batman\n"
        "• the boys\n\n"

        "📡 Bot sẽ tự tìm ở:\n"
        "• SERVER 1 (Vietsub)\n"
        "• SERVER 2 (Vietsub + Thuyết Minh)\n"
        "• SERVER 3 (Vietsub + Lồng Tiếng)"
    )

    await update.message.reply_text(text)

# =====================================================
# MENU COMMANDS
# =====================================================

async def setup_commands(app):

    commands = [

        BotCommand(
            "start",
            "Khởi động bot"
        ),
    ]

    await app.bot.set_my_commands(commands)

# =====================================================
# SEARCH
# =====================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyword = update.message.text.strip()

    if not keyword:
        return

    wait_msg = await update.message.reply_text(
        "🔎 Đang tìm phim..."
    )

    found_any = False

    # =================================================
    # SERVER 1
    # =================================================

    try:

        url = (
            SOURCES["1"]["search"]
            + keyword
        )

        r = await client.get(url)

        data = r.json()

        movies = data.get(
            "items",
            []
        )

        if movies:

            found_any = True

            keyboard = []

            for movie in movies[:5]:

                name = movie.get(
                    "name",
                    "Không tên"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        name,
                        callback_data=(
                            f"1|{movie.get('slug', '')}"
                        )
                    )
                ])

            await update.message.reply_text(
                "📡 SERVER 1 (Vietsub)",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

    except Exception as e:

        print("SERVER 1 ERROR:", e)

    # =================================================
    # SERVER 2
    # =================================================

    try:

        url = (
            SOURCES["2"]["search"]
            + keyword
        )

        r = await client.get(url)

        data = r.json()

        movies = (
            data.get("data", {})
            .get("items", [])
        )

        if movies:

            found_any = True

            keyboard = []

            for movie in movies[:5]:

                name = movie.get(
                    "name",
                    "Không tên"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        name,
                        callback_data=(
                            f"2|{movie.get('slug', '')}"
                        )
                    )
                ])

            # =========================
            # CHECK THUYET MINH
            # =========================

            server_label = "📡 SERVER 2"

            movie_text = str(movies).lower()

            if (
                "thuyết minh" in movie_text
                or "thuyet minh" in movie_text
            ):

                server_label += (
                    " (Vietsub + Thuyết Minh)"
                )

            else:

                server_label += (
                    " (Vietsub)"
                )

            await update.message.reply_text(
                server_label,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

    except Exception as e:

        print("SERVER 2 ERROR:", e)

    # =================================================
    # SERVER 3
    # =================================================

    try:

        url = (
            SOURCES["3"]["search"]
            + keyword
        )

        r = await client.get(url)

        data = r.json()

        movies = (
            data.get("data", {})
            .get("items", [])
        )

        if movies:

            found_any = True

            keyboard = []

            for movie in movies[:5]:

                name = movie.get(
                    "name",
                    "Không tên"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        name,
                        callback_data=(
                            f"3|{movie.get('slug', '')}"
                        )
                    )
                ])

            # =========================
            # CHECK LONG TIENG
            # =========================

            server_label = "📡 SERVER 3"

            movie_text = str(movies).lower()

            if (
                "lồng tiếng" in movie_text
                or "long tieng" in movie_text
            ):

                server_label += (
                    " (Vietsub + Lồng Tiếng)"
                )

            else:

                server_label += (
                    " (Vietsub)"
                )

            await update.message.reply_text(
                server_label,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

    except Exception as e:

        print("SERVER 3 ERROR:", e)

    # =================================================
    # NO RESULT
    # =================================================

    if not found_any:

        await wait_msg.edit_text(
            "❌ Không tìm thấy phim!"
        )

    else:

        await wait_msg.delete()
# =====================================================
# MOVIE DETAIL
# =====================================================

async def movie_detail(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    source_id, slug = (
        query.data.split("|")
    )

    try:

        # =================================================
        # NGUONC
        # =================================================

        if source_id == "1":

            detail_url = (
                SOURCES["1"]["detail"]
                + slug
            )

            r = await client.get(
                detail_url
            )

            data = r.json()

            movie = data.get(
                "movie",
                {}
            )

            episodes = data.get(
                "episodes",
                []
            )

            if not episodes:

                episodes = movie.get(
                    "episodes",
                    []
                )

            name = movie.get(
                "name",
                "Không tên"
            )

            poster = (
                movie.get("poster_url")
                or movie.get("thumb_url")
            )

            text = (
                f"🎬 {name}\n\n"
            )

            found = False

            for server in episodes:

                server_name = server.get(
                    "server_name",
                    "Server"
                )

                items = server.get(
                    "items",
                    []
                )

                for ep in items:

                    ep_name = ep.get(
                        "name",
                        "FULL"
                    )

                    embed = ep.get(
                        "embed",
                        ""
                    )

                    if embed:

                        found = True

                        text += (
                            f"🎞 {ep_name}\n"
                            f"📡 {server_name}\n\n"
                            f"🎬 XEM NGAY:\n"
                            f"{embed}\n\n"
                        )

            if not found:

                text += (
                    "❌ Không tìm thấy player"
                )

        # =================================================
        # OPHIM + KKPHIM
        # =================================================

        else:

            detail_url = (
                SOURCES[source_id]["detail"]
                + slug
            )

            r = await client.get(
                detail_url
            )

            data = r.json()

            movie = data.get(
                "movie",
                {}
            )

            episodes = data.get(
                "episodes",
                []
            )

            name = movie.get(
                "name",
                "Không tên"
            )

            poster = (
                movie.get("poster_url")
                or movie.get("thumb_url")
            )

            if (
                poster
                and not poster.startswith(
                    "http"
                )
            ):

                poster = (
                    "https://phimimg.com/"
                    + poster.lstrip("/")
                )

            text = (
                f"🎬 {name}\n\n"
            )

            found = False

            for server in episodes:

                server_name = server.get(
                    "server_name",
                    "Server"
                )

                items = (
                    server.get(
                        "server_data",
                        []
                    )
                    or server.get(
                        "items",
                        []
                    )
                )

                for ep in items:

                    ep_name = ep.get(
                        "name",
                        "FULL"
                    )

                    embed = (
                        ep.get(
                            "link_embed"
                        )
                        or ep.get(
                            "embed"
                        )
                    )

                    if embed:

                        found = True

                        text += (
                            f"🎞 {ep_name}\n"
                            f"📡 {server_name}\n\n"
                            f"🎬 XEM NGAY:\n"
                            f"{embed}\n\n"
                        )

            if not found:

                text += (
                    "❌ Không tìm thấy player"
                )

        # =====================================================
        # SEND
        # =====================================================

        if poster:

            try:

                await query.message.reply_photo(
                    photo=poster,
                    caption=text
                )

            except Exception as e:

                print(e)

                await query.message.reply_text(
                    text
                )

        else:

            await query.message.reply_text(
                text
            )

    except Exception as e:

        print(e)

        await query.message.reply_text(
            f"❌ Lỗi lấy thông tin phim!\n\n{e}"
        )

# =====================================================
# MAIN
# =====================================================

if not TOKEN:
    raise ValueError(
        "Thiếu BOT_TOKEN"
    )

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .build()
)

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT
        & ~filters.COMMAND,
        search
    )
)

app.add_handler(
    CallbackQueryHandler(
        movie_detail
    )
)

app.post_init = setup_commands

print("BOT STARTING...")
print("Bot đang chạy...")

async def main():

    await app.initialize()

    await app.start()

    await app.updater.start_polling(
        drop_pending_updates=True
    )

    print("BOT ĐÃ ONLINE")

    while True:
        await asyncio.sleep(3600)

asyncio.run(main())
