import asyncio
import os
import base64
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Бот берет токен из переменной окружения LIVPN_TOKEN
TOKEN = os.getenv('LIVPN_TOKEN')

if not TOKEN:
    print("Ошибка: Переменная LIVPN_TOKEN не установлена!")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище лимитов (в памяти сервера)
user_data = {}

def generate_awg_config():
    priv_key = base64.b64encode(os.urandom(32)).decode()
    config = f"""[Interface]
PrivateKey = {priv_key}
Address = 172.16.0.2/32
DNS = 1.1.1.1
Jc = 120
Jmin = 23
Jmax = 911
S1 = 15
S2 = 24
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=
Endpoint = engage.cloudflareclient.com:2408
AllowedIPs = 0.0.0.0/0"""
    return config

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Подключиться", callback_data="connect"))
    builder.row(types.InlineKeyboardButton(text="❓ Как работает VPN?", callback_data="how_it_works"))
    builder.row(types.InlineKeyboardButton(text="🌐 Сайты, которые разблокированы", callback_data="sites"))
    
    await message.answer(
        "👋 Привет! Это **LiVPN**.\nНажми на кнопку ниже, чтобы получить настройки.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "connect")
async def handle_connect(callback: types.CallbackQuery):
    uid = callback.from_user.id
    count = user_data.get(uid, 0)

    if count >= 15:
        await callback.answer("Лимит 15 подключений исчерпан!", show_alert=True)
        return

    user_data[uid] = count + 1
    config_text = generate_awg_config()
    file_name = f"LiVPN_v{count + 1}.conf"
    
    with open(file_name, "w") as f:
        f.write(config_text)

    await callback.message.answer_document(
        types.FSInputFile(file_name),
        caption=f"✅ Подключение #{count + 1} из 15\n\nИспользуй приложение **AmneziaWG**."
    )
    os.remove(file_name)
    await callback.answer()

@dp.callback_query(F.data == "how_it_works")
async def handle_how(callback: types.CallbackQuery):
    text = (
        "Мы работаем на серверах Cloudflare. Когда вы подключаетесь к VPN, мы ищем самый близкий сервер к нам, "
        "и шифруем трафик. Также, наш впн ЧАСТИЧНО обходит белые списки. Интернет становится работать хуже, "
        "но доступ к ограниченным сервисам возвращается (я про белые списки)."
    )
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "sites")
async def handle_sites(callback: types.CallbackQuery):
    sites = (
        "📍 **Список разблокированных ресурсов:**\n\n"
        "• YouTube, Instagram, Discord\n• Modrinth, Signal\n• Звонки в Telegram и WhatsApp\n"
        "• InfinityFree, Чёрно Оранжевый ютуб, Twitter (X), Facebook\n"
        "• Ficbook, Rutracker, Rutor, Proton, Zetfix, Canva\n"
        "• ChatGPT, Gemini, Copilot, Patreon, Viber\n\n"
        "🏛 Также работают гос приложения и банки."
    )
    await callback.message.answer(sites, parse_mode="Markdown")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())