import asyncio
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from main.hendlers import router as hendlers_router
from main.hendlers_python import router as hendlers_router1
from main.hendlers_robotics import router as hendlers_router2
from main.inostranio import router as hendlers_router3
from main.my_command import router as hendlers_router4
from main.play1 import router as hendlers_router5
from main.play2 import router as hendlers_router6
from database import init_answer, init_play  

load_dotenv()
token = os.getenv("TOKEN")

dp = Dispatcher()
dp.include_routers(
    hendlers_router, 
    hendlers_router1, 
    hendlers_router2, 
    hendlers_router3, 
    hendlers_router4, 
    hendlers_router5, 
    hendlers_router6
)

async def handle(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")


async def pinger():
    """Функция, которая сама пингует сайт бота каждые 10 минут"""
    await asyncio.sleep(10)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get('https://bot-api-8gls.onrender.com') as response:
                    print(f"Пинг выполнен! Статус: {response.status}")
            except Exception as e:
                print(f"Ошибка пинга: {e}")
            await asyncio.sleep(600) # 600 секунд = 10 минут

async def main():
    await start_web_server()

    asyncio.create_task(pinger())

    bot = Bot(token)
    print("Инициализация таблиц базы данных...")
    await init_answer() 
    await init_play()
    print("Все таблицы успешно созданы и готовы к работе!")

    print("Бот успешно запущен, пингер работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен!")
