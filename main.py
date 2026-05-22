import logging
import httpx
from urllib.parse import quote
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from html import escape

# 1. Logging chuẩn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = 'YOUR_TOKEN'
# 3. Global Session tái sử dụng
client = httpx.AsyncClient(timeout=10)

SOURCES = {
    '1': {'url': 'https://api.nguonc.com/api/films/search?keyword=', 'base_link': 'https://nguonc.com/phim/'},
    '2': {'url': 'https://api.kkphim.com/api/films/search?keyword=', 'base_link': 'https://kkphim.com/phim/'},
    '3': {'url': 'https://ophim1.com/v1/api/tim-kiem?keyword=', 'base_link': 'https://ophim1.com/phim/'}
}

async def tim_phim(source_id, keyword):
    source = SOURCES.get(source_id)
    if not source: return None
    
    try:
        # 1 & 2. Check status và decode an toàn
        res = await client.get(source['url'] + quote(keyword))
        res.raise_for_status()
        data = res.json()
        items = data.get('data', {}).get('items') or data.get('items') or []
        return items[:5] # Chỉ lấy 5 kết quả đầu để tránh tràn keyboard
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 4. Command parsing không hacky
    cmd_parts = update.message.text.split(maxsplit=1)
    if len(cmd_parts) < 2:
        await update.message.reply_text("Cú pháp: /<nguồn> [tên phim]\nVí dụ: /3 Batman")
        return
    
    source_id = cmd_parts[0][1:]
    keyword = cmd_parts[1]
    
    movies = await tim_phim(source_id, keyword)
    
    if not movies:
        await update.message.reply_text("Không tìm thấy hoặc nguồn lỗi!")
        return

    # 5. Inline Keyboard (Giải quyết bottleneck UX)
    keyboard = []
    for m in movies:
        # Lưu slug vào callback_data để khi bấm thì truy xuất lại
        callback_data = f"view|{source_id}|{m.get('slug')}"
        keyboard.append([InlineKeyboardButton(m.get('name'), callback_data=callback_data)])
    
    await update.message.reply_text("Chọn phim bạn muốn xem:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, source_id, slug = query.data.split('|')
    
    # Ở đây bạn fetch chi tiết phim dựa trên slug và gửi cho user
    await query.answer()
    await query.edit_message_text(f"Đang lấy link chi tiết cho phim: {slug} từ nguồn {source_id}...")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(['1', '2', '3'], search))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot Production Ready!")
    app.run_polling()
