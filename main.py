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
# TOKEN
# =====================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Thiếu BOT_TOKEN")

print("BOT STARTING...")

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
        "🎬 CHÀO MỪNG ĐẾN VỚI SUPER BOT FILM\n\n"

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
# COMMANDS
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

    for sid in ["1", "2", "3"]:

        try:

            url = (
                SOURCES[sid]["search"]
                + keyword
            )

            r = await client.get(url)

            data = r.json()

            if sid == "1":

                movies = data.get(
                    "items",
                    []
                )

            else:

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
                                f"{sid}|{movie.get('slug', '')}"
                            )
                        )
                    ])

                server_label = f"📡 SERVER {sid}"

                movie_text = str(movies).lower()

                if sid == "2":

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

                if sid == "3":

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

            print(f"SERVER {sid} ERROR:", e)

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

        episodes = (
            data.get("episodes", [])
            or movie.get("episodes", [])
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
            and not poster.startswith("http")
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

            items = server.get(
                "server_data",
                []
            )

            if not items:

                items = server.get(
                    "items",
                    []
                )

            for ep in items:

                print(ep)

                ep_name = ep.get(
                    "name",
                    "FULL"
                )

                embed = (
                    ep.get("link_embed")
                    or ep.get("link_m3u8")
                    or ep.get("embed")
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
        # SEND
        # =================================================

        if poster:

            try:

                await query.message.reply_photo(
                    photo=poster
                )

            except Exception as e:

                print("PHOTO ERROR:", e)

        await query.message.reply_text(
            text[:4000]
        )

    except Exception as e:

        print("MOVIE DETAIL ERROR:", e)

        await query.message.reply_text(
            f"❌ Lỗi lấy thông tin phim!\n\n{e}"
        )

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    asyncio.set_event_loop(
        asyncio.new_event_loop()
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
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            movie_detail
        )
    )

    app.post_init = setup_commands

    PORT = int(
        os.environ.get("PORT", 10000)
    )

    APP_NAME = "movie-bot-super"

    WEBHOOK_SECRET = "superbotfilm"

    print("BOT STARTING WITH WEBHOOK...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=f"webhook/{WEBHOOK_SECRET}",
        webhook_url=(
            f"https://{APP_NAME}.onrender.com/"
            f"webhook/{WEBHOOK_SECRET}"
        ),
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
