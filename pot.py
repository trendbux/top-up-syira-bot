import os
import asyncio
import aiosqlite

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")


DB = "top_up_syira.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0
            )
        """)

        await db.commit()


async def add_user(user_id, username):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username)
            VALUES (?, ?)
        """, (user_id, username))

        await db.commit()


async def get_balance(user_id):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE id = ?",
            (user_id,)
        )

        row = await cursor.fetchone()

        if row:
            return row[0]

        return 0


def main_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(text="🛒 الخدمات", callback_data="services")
    kb.button(text="💰 رصيدي", callback_data="balance")
    kb.button(text="💳 شحن الرصيد", callback_data="deposit")
    kb.button(text="📦 طلباتي", callback_data="orders")

    kb.adjust(2)

    return kb.as_markup()


@dp.message(CommandStart())
async def start(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username
    )

    await message.answer(
        "🇸🇾 <b>أهلاً بك في Top Up Syira</b>\n\n"
        "خدمات السوشيال ميديا بأسعار مناسبة.\n\n"
        "اختر من القائمة:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):

    balance = await get_balance(callback.from_user.id)

    await callback.answer()

    await callback.message.edit_text(
        f"💰 <b>رصيدك الحالي</b>\n\n"
        f"💵 {balance:.2f}$",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "services")
async def services(callback: CallbackQuery):

    kb = InlineKeyboardBuilder()

    kb.button(
        text="📸 Instagram",
        callback_data="instagram"
    )

    kb.button(
        text="🎵 TikTok",
        callback_data="tiktok"
    )

    kb.button(
        text="▶️ YouTube",
        callback_data="youtube"
    )

    kb.button(
        text="📢 Telegram",
        callback_data="telegram"
    )

    kb.button(
        text="🔙 رجوع",
        callback_data="home"
    )

    kb.adjust(2)

    await callback.answer()

    await callback.message.edit_text(
        "🛒 <b>خدمات Top Up Syira</b>\n\n"
        "اختر المنصة:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.in_({
    "instagram",
    "tiktok",
    "youtube",
    "telegram"
}))
async def platform(callback: CallbackQuery):

    names = {
        "instagram": "📸 Instagram",
        "tiktok": "🎵 TikTok",
        "youtube": "▶️ YouTube",
        "telegram": "📢 Telegram"
    }

    platform_name = names[callback.data]

    await callback.answer()

    await callback.message.edit_text(
        f"{platform_name}\n\n"
        "🚧 الخدمات والأسعار سيتم ربطها تلقائياً "
        "من مزود الخدمة في الخطوة القادمة.\n\n"
        "انتظر قليلاً، عم نبني النظام لك.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "deposit")
async def deposit(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "💳 <b>شحن الرصيد</b>\n\n"
        "قم بالتحويل إلى إحدى طرق الدفع الخاصة بنا، "
        "ثم أرسل إثبات التحويل.\n\n"
        "بعد مراجعة التحويل من الإدارة، "
        "سيتم إضافة الرصيد إلى حسابك يدوياً.\n\n"
        "📌 الدفع ليس تلقائياً.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "📦 <b>طلباتي</b>\n\n"
        "لا توجد طلبات حالياً.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "🇸🇾 <b>Top Up Syira</b>\n\n"
        "اختر من القائمة:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


async def health(request):
    return web.Response(text="Top Up Syira is running!")


async def start_web_server():
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(os.getenv("PORT", "10000"))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()


async def main():

    await init_db()

    await start_web_server()

    print("🇸🇾 Top Up Syira is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
