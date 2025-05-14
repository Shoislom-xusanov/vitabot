import asyncio
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.client.default import DefaultBotProperties

# 🔐 TOKEN va ADMIN ID — faqat shu yerlarni o'zgartirasiz
TOKEN = "7684681301:AAESh_iADrmuGhJEk8698tX55uuxGq8pwxY"
ADMIN_ID = 2055602037

# Bot va dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Mahsulotlarni yuklash
def load_products():
    products_file = Path("products.json")
    if not products_file.exists():
        return []
    with open(products_file, "r", encoding="utf-8") as f:
        return json.load(f)

# Holatlar
class Order(StatesGroup):
    name = State()
    phone = State()
    address = State()

# /start komandasi
@dp.message(CommandStart())
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Mahsulotlarni ko‘rish", callback_data="show_product")
    await message.answer("Assalomu alaykum!\nMahsulotlar bilan tanishing:", reply_markup=builder.as_markup())

# Mahsulotlarni chiqarish
@dp.callback_query(lambda c: c.data == "show_product")
async def show_products(call: CallbackQuery):
    products = load_products()
    for product in products:
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Buyurtma berish", callback_data=f"order_{product['id']}")
        image_path = product.get("image_path")
        if not image_path:
            continue
        image = FSInputFile(image_path)
        await call.message.answer_photo(
            photo=image,
            caption=f"<b>{product['name']}</b>\n💵 {product['price']}",
            reply_markup=builder.as_markup()
        )

# Buyurtma bosqichlari
@dp.callback_query(lambda c: c.data.startswith("order_"))
async def order_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Order.name)
    await call.message.answer("Ismingizni kiriting:")

@dp.message(StateFilter(Order.name))
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Order.phone)
    await message.answer("Telefon raqamingizni kiriting:")

@dp.message(StateFilter(Order.phone))
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Order.address)
    await message.answer("Manzil yoki izoh qoldiring (lokatsiya yuborsangiz ham bo‘ladi):")

@dp.message(StateFilter(Order.address))
async def get_address(message: Message, state: FSMContext):
    import html
    data = await state.get_data()
    name = html.escape(data.get("name"))
    phone = html.escape(data.get("phone"))
    username = html.escape(message.from_user.username) if message.from_user.username else "yo‘q"

    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        address = f"📍 <a href='https://www.google.com/maps/search/?api=1&query={lat},{lon}'>Lokatsiya yuborildi</a>"
    else:
        address = html.escape(message.text)

    msg = (
        f"📦 <b>Yangi buyurtma!</b>\n\n"
        f"<b>👤 Ism:</b> {name}\n"
        f"<b>📞 Tel:</b> {phone}\n"
        f"{address}\n"
        f"<b>📩 Telegram:</b> @{username}"
    )

    await bot.send_message(chat_id=ADMIN_ID, text=msg)
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz.")
    await state.clear()

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
