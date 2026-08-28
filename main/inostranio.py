import os
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from state.state import pogodai, fakti, escursi, cursi
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import aiohttp
from xml.etree import ElementTree

load_dotenv()
API = os.getenv("api")
router = Router()
YANDEX_NS = "{http://yandex.com/xml}"

async def yandex_api(query: str) -> str:
    """Запрос к Яндекс.Поиск API (XML)"""
    url = "https://yandex.com/search/xml"
    params = {
        "user": "Keksik25092015",
        "key": API,
        "query": query,
        "lr": 1, 
        "l10n": "ru",
        "sortby": "rlv"
    }

    timeout = aiohttp.ClientTimeout(total=5)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    xml_text = await response.text()
                    root = ElementTree.fromstring(xml_text)
                    
                    results = []
                    for doc in root.findall(f'{YANDEX_NS}.//doc'):
                        title = doc.findtext(f'{YANDEX_NS}title', '')
                        snippet = doc.findtext(f'{YANDEX_NS}headline', '') or doc.findtext(f'{YANDEX_NS}passages', '')
                        url_result = doc.findtext(f'{YANDEX_NS}url', '')
                    
                        if title:
                            results.append(f"🔹 {title}\n{snippet[:200]}\n🔗 {url_result}\n")
                    
                    if results:
                        return "Результаты поиска:\n\n" + "\n".join(results[:5])
                    else:
                        return "Ничего не найдено"
                else:
                    return f"Ошибка Яндекс API (Код {response.status}). Проверь IP сервера в кабинете Яндекс.XML!"
    except asyncio.TimeoutError:
        return "⚠️ Яндекс не ответил за 5 секунд. Попробуй ещё раз!"
    except Exception as e:
        return f"⚠️ Ошибка запроса: {e}"


# Погода
@router.message(Command("pogoda"))
async def cmdo(message: Message, state: FSMContext):
    await message.answer("Введите остров/город/село в котором хотите узнать погоду")
    await state.set_state(pogodai.strana)


@router.message(pogodai.strana)
async def sroko(message: Message, state: FSMContext):
    await state.update_data(strana=message.text)
    await message.answer("Введите срок на который нужно узнать погоду например сегодня, завтра, 3 дня и т.д")
    await state.set_state(pogodai.srok)

@router.message(pogodai.srok)
async def sroki(message: Message, state: FSMContext):
    await state.update_data(srok=message.text)
    data1 = await state.get_data()
    strana = data1.get('strana')
    srok = data1.get('srok')
    full1 = f"Погода {strana} на {srok}"
    await message.answer(f"Ищу {full1}")
    result = await yandex_api(full1)
    await message.answer(result)
    await state.clear()
    

# Экскурсия
@router.message(Command("escurs"))
async def cd(message: Message, state: FSMContext):
    await message.answer("Введите страну/область/остров и т.д в которой хотите узнать про популярные экскурсии")
    await state.set_state(escursi.strana)


@router.message(escursi.strana)
async def sr(message: Message, state: FSMContext):
    await state.update_data(strana=message.text)
    await message.answer("Введите количество экскурсий")
    await state.set_state(escursi.col)


@router.message(escursi.col)
async def o(message: Message, state: FSMContext):
    await state.update_data(col=message.text)
    data3 = await state.get_data()
    strana = data3.get('strana')
    col2 = data3.get('col')
    full3 = f"Популярные экскурсии в {strana} {col2} вариантов"
    await message.answer(f"Ищу {full3}")
    result = await yandex_api(full3)
    await message.answer(result)
    await state.clear()

# Курс
@router.message(Command("curs"))
async def md(message: Message, state: FSMContext):
    await message.answer("Введите валюту в которую будете переводить")
    await state.set_state(cursi.vala)

@router.message(cursi.vala)
async def ro(message: Message, state: FSMContext):
    await state.update_data(vala=message.text)
    await message.answer("Введите валюту из которой будете переводить")
    await state.set_state(cursi.valb)

@router.message(cursi.valb)
async def cm(message: Message, state: FSMContext):
    await state.update_data(valb=message.text)
    await message.answer("Введите количество которое нужно перевести")
    await state.set_state(cursi.col)


@router.message(cursi.col)
async def sro(message: Message, state: FSMContext):
    await state.update_data(col=message.text)
    data4 = await state.get_data()
    vala = data4.get('vala')
    valb = data4.get('valb')
    col3 = data4.get('col')
    full4 = f"Сколько {col3} {valb} в {vala}"
    await message.answer(f"Ищу {full4}")
    result = await yandex_api(full4)
    await message.answer(result)
    await state.clear()
