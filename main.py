import logging
import asyncio
import os
import requests
import ijson
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("LIVPN_TOKEN")
# Твоя новая постоянная ссылка
GITHUB_JSON_URL = "https://raw.githubusercontent.com/mopidplus-max/LiVPNbot/refs/heads/main/ip-list.json"
WORKING_PRIV_KEY = "qMvr//6Muy5NMQS4dblx3qyTbYbSEUMdLc3KJdeJOXc="

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА ОБРАБОТКИ ТЯЖЕЛОГО JSON ---

def get_allowed_ips_stream(site_key):
    """Потоковое чтение JSON: ищем только нужный сайт, не забивая память"""
    if site_key == "all":
        return "0.0.0.0/0, ::/0"
        
    try:
        # stream=True позволяет скачивать файл по кусочкам
        with requests.get(GITHUB_JSON_URL, stream=True, timeout=20) as r:
            r.raise_for_status()
            # ijson.kvitems читает пары ключ-значение прямо из потока байтов
            parser = ijson.kvitems(r.raw, '')
            for key, value in parser:
                if key == site_key:
                    # Извлекаем данные согласно структуре твоего файла
                    ips = value.get('cidr4', []) + value.get('cidr6', [])
                    if not ips:
                        ips = value.get('ip4', []) + value.get('ip6', [])
                    return ", ".join(ips) if ips else "0.0.0.0/0, ::/0"
    except Exception as e:
        logging.error(f"Ошибка при поиске в JSON: {e}")
    
    return "0.0.0.0/0, ::/0"

def generate_config(dns, endpoint, site_key):
    """Создание текста конфига AmneziaWG"""
    allowed_ips = get_allowed_ips_stream(site_key)
    return f"""[Interface]
PrivateKey = {WORKING_PRIV_KEY}
Address = 172.16.0.2/32, 2606:4700:110:8fd1:c3d9:c0fc:b3e5:956d
DNS = {dns}
MTU = 1280
S1 = 0
S2 = 0
Jc = 120
Jmin = 23
Jmax = 911
H1 = 1
H2 = 2
H3 = 3
H4 = 4
I1 = <b 0xc10000000114367096bb0fb3f58f3a3fb8aaacd61d63a1c8a40e14f7374b8a62dccba6431716c3abf6f5afbcfb39bd008000047c32e268567c652e6f4db58bff759bc8c5aaca183b87cb4d22938fe7d8dca22a679a79e4d9ee62e4bbb3a380dd78d4e8e48f26b38a1d42d76b371a5a9a0444827a69d1ab5872a85749f65a4104e931740b4dc1e2dd77733fc7fac4f93011cd622f2bb47e85f71992e2d585f8dc765a7a12ddeb879746a267393ad023d267c4bd79f258703e27345155268bd3cc0506ebd72e2e3c6b5b0f005299cd94b67ddabe30389c4f9b5c2d512dcc298c14f14e9b7f931e1dc397926c31fbb7cebfc668349c218672501031ecce151d4cb03c4c660b6c6fe7754e75446cd7de09a8c81030c5f6fb377203f551864f3d83e27de7b86499736cbbb549b2f37f436db1cae0a4ea39930f0534aacdd1e3534bc87877e2afabe959ced261f228d6362e6fd277c88c312d966c8b9f67e4a92e757773db0b0862fb8108d1d8fa262a40a1b4171961f0704c8ba314da2482ac8ed9bd28d4b50f7432d89fd800c25a50c5e2f5c0710544fef5273401116aa0572366d8e49ad758fcb29e6a92912e644dbe227c247cb3417eabfab2db16796b2fba420de3b1dc94e8361f1f324a331ddaf1e626553138860757fd0bf687566108b77b70fb9f8f8962eca599c4a70ed373666961a8cb506b96756d9e28b94122b20f16b54f118c0e603ce0b831efea614ad836df6cf9affbdd09596412547496967da758cec9080295d853b0861670b71d9abde0d562b1a6de82782a5b0c14d297f27283a895abc889a5f6703f0e6eb95f67b2da45f150d0d8ab805612d570c2d5cb6997ac3a7756226c2f5c8982ffbd480c5004b0660a3c9468945efde90864019a2b519458724b55d766e16b0da25c0557c01f3c11ddeb024b62e303640e17fdd57dedb3aeb4a2c1b7c93059f9c1d7118d77caac1cd0f6556e46cbc991c1bb16970273dea833d01e5090d061a0c6d25af2415cd2878af97f6d0e7f1f936247b394ecb9bd484da6be936dee9b0b92dc90101a1b4295e97a9772f2263eb09431995aa173df4ca2abd687d87706f0f93eaa5e13cbe3b574fa3cfe94502ace25265778da6960d561381769c24e0cbd7aac73c16f95ae74ff7ec38124f7c722b9cb151d4b6841343f29be8f35145e1b27021056820fed77003df8554b4155716c8cf6049ef5e318481460a8ce3be7c7bfac695255be84dc491c19e9dedc449dd3471728cd2a3ee51324ccb3eef121e3e08f8e18f0006ea8957371d9f2f739f0b89e4db11e5c6430ada61572e589519fbad4498b460ce6e4407fc2d8f2dd4293a50a0cb8fcaaf35cd9a8cc097e3603fbfa08d9036f52b3e7fcce11b83ad28a4ac12dba0395a0cc871cefd1a2856fffb3f28d82ce35cf80579974778bab13d9b3578d8c75a2d196087a2cd439aff2bb33f2db24ac175fff4ed91d36a4cdbfaf3f83074f03894ea40f17034629890da3efdbb41141b38368ab532209b69f057ddc559c19bc8ae62bf3fd564c9a35d9a83d14a95834a92bae6d9a29ae5e8ece07910d16433e4c6230c9bd7d68b47de0de9843988af6dc88b5301820443bd4d0537778bf6b4c1dd067fcf14b81015f2a67c7f2a28f9cb7e0684d3cb4b1c24d9b343122a086611b489532f1c3a26779da1706c6759d96d8ab>

[Peer]
PublicKey = bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=
AllowedIPs = {allowed_ips}
Endpoint = {endpoint}
"""

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **LiVPN приветствует тебя!**\n\n"
        "• /getvpn — создать конфиг\n"
        "• Напиши название сайта (например, `YouTube`), чтобы проверить его доступность."
    )

@dp.message(Command("getvpn"))
async def vpn_dns(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Cloudflare DNS", callback_data="dns_1.1.1.1")
    builder.button(text="Google DNS", callback_data="dns_8.8.8.8")
    builder.adjust(2)
    await message.answer("🎯 **Шаг 1: DNS**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("dns_"))
async def vpn_ep(callback: types.CallbackQuery):
    dns = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.button(text="Порт 2408", callback_data=f"ep_{dns}_162.159.193.5:2408")
    builder.button(text="Порт 4500", callback_data=f"ep_{dns}_engage.cloudflareclient.com:4500")
    builder.adjust(1)
    await callback.message.edit_text("🌐 **Шаг 2: Эндпоинт**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ep_"))
async def vpn_mode(callback: types.CallbackQuery):
    _, dns, ep = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Весь трафик", callback_data=f"fin_{dns}_{ep}_all")
    # Список популярных ключей из твоего JSON
    popular = ["amedia.site", "anidub.pro", "anilibria.tv", "animego.org", "crunchyroll.com"]
    for p in popular:
        builder.button(text=f"Только {p}", callback_data=f"fin_{dns}_{ep}_{p}")
    builder.adjust(1)
    await callback.message.edit_text("🛡 **Шаг 3: Режим работы**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fin_"))
async def vpn_finish(callback: types.CallbackQuery):
    _, dns, ep, site = callback.data.split("_")
    await callback.message.edit_text("⏳ Генерирую конфиг... Это займет пару секунд.")
    
    config_text = generate_config(dns, ep, site)
    file_name = f"LiVPN_{site.split('.')[0]}.conf"
    config_file = types.BufferedInputFile(config_text.encode('utf-8'), filename=file_name)
    
    await callback.message.answer_document(config_file, caption=f"✅ Готово!\n📍 Режим: {site}")
    await callback.answer()

@dp.message()
async def check_service(message: types.Message):
    query = message.text.lower().strip()
    msg = await message.answer("🔍 Проверяю базу данных...")
    
    found = False
    try:
        with requests.get(GITHUB_JSON_URL, stream=True, timeout=15) as r:
            parser = ijson.kvitems(r.raw, '')
            for key, info in parser:
                # Сверяем по ключу или имени
                if query in key.lower() or query in info.get('name', '').lower():
                    await msg.edit_text(f"✅ Да! Ваш сервис **{info.get('name', key)}** работает с нашим VPN.")
                    found = True
                    break
    except Exception as e:
        logging.error(f"Search error: {e}")
            
    if not found:
        await msg.edit_text("❌ К сожалению, этого сервиса нет в списке оптимизированных, но он будет работать в режиме 'Весь трафик'.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
