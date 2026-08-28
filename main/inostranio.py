import os
import wikipedia
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import requests
from json import JSONDecodeError

from state.state import pogodai, fakti, escursi, cursi

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# Настройка языка Wikipedia (русский)
wikipedia.set_lang("ru")


async def wiki_search(query: str) -> str:
    """Ищет информацию по Википедии, защищена от ошибок JSON"""
    url = "https://ru.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": "1"
    }
    
    # Представляемся обычным браузером Chrome, чтобы Википедия отдавала чистый JSON:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=5) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                    except Exception:
                        return f"ℹ️ Не удалось распарсить ответ для '{query}'."

                    search_results = data.get("query", {}).get("search", [])
                    
                    if not search_results:
                        return f"❌ По запросу '{query}' ничего не найдено."
                    
                    lines = []
                    for item in search_results[:3]:
                        title = item.get("title", "")
                        # Очищаем текст от HTML-тегов Википедии:
                        snippet = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '').replace('&quot;', '"')
                        encoded_title = urllib.parse.quote(title)
                        link = f"https://ru.wikipedia.org/wiki/{encoded_title}"
                        
                        lines.append(f"🔹 *{title}*\n{snippet}...\n🔗 [Читать в Википедии]({link})\n")
                    
                    return "🔎 *Результаты:*\n\n" + "\n".join(lines)
                else:
                    return f"⚠️ Википедия ответила со статусом: {response.status}"
    except Exception as e:
        return f"⚠️ Ошибка сети: {e}"



# ---------------------------
# Погода
# ---------------------------
@router.message(Command("pogoda"))
async def cmd_pogoda_start(message: Message, state: FSMContext):
    await message.answer("Введите остров/город/село, в котором хотите узнать погоду.")
    await state.set_state(pogodai.strana)


@router.message(pogodai.strana)
async def pogoda_strana_handler(message: Message, state: FSMContext):
    await state.update_data(strana=message.text)
    await message.answer(
        "Введите срок, на который нужно узнать погоду (например: сегодня, завтра, 3 дня)."
    )
    await state.set_state(pogodai.srok)


@router.message(pogodai.srok)
async def pogoda_srok_handler(message: Message, state: FSMContext):
    await state.update_data(srok=message.text)
    data = await state.get_data()

    strana = data.get("strana", "")
    srok = data.get("srok", "")
    query = f"Погода {strana}"

    await message.answer(f"Ищу: {query}")
    result = wiki_search(query, sentences=3)
    await message.answer(result)
    await state.clear()


# ---------------------------
# Экскурсии
# ---------------------------
@router.message(Command("escurs"))
async def cmd_escurs_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите страну/область/остров, в которой хотите узнать про популярные экскурсии."
    )
    await state.set_state(escursi.strana)


@router.message(escursi.strana)
async def escurs_strana_handler(message: Message, state: FSMContext):
    await state.update_data(strana=message.text)
    await message.answer("Введите количество экскурсий.")
    await state.set_state(escursi.col)


@router.message(escursi.col)
async def escurs_col_handler(message: Message, state: FSMContext):
    await state.update_data(col=message.text)
    data = await state.get_data()

    strana = data.get("strana", "")
    col = data.get("col", "")
    query = f"Экскурсии {strana}"

    await message.answer(f"Ищу: {query}")
    result = wiki_search(query, sentences=3)
    await message.answer(result)
    await state.clear()


# ---------------------------
# Курс валют
# ---------------------------
@router.message(Command("curs"))
async def cmd_curs_start(message: Message, state: FSMContext):
    await message.answer("Введите валюту, в которую будете переводить (например: USD).")
    await state.set_state(cursi.vala)


@router.message(cursi.vala)
async def curs_vala_handler(message: Message, state: FSMContext):
    await state.update_data(vala=message.text)
    await message.answer("Введите валюту, из которой будете переводить (например: RUB).")
    await state.set_state(cursi.valb)


@router.message(cursi.valb)
async def curs_valb_handler(message: Message, state: FSMContext):
    await state.update_data(valb=message.text)
    await message.answer("Введите количество, которое нужно перевести.")
    await state.set_state(cursi.col)


@router.message(cursi.col)
async def curs_col_handler(message: Message, state: FSMContext):
    await state.update_data(col=message.text)
    data = await state.get_data()

    vala = data.get("vala", "")
    valb = data.get("valb", "")
    col = data.get("col", "")
    query = f"Курс валют {valb} к {vala}"

    await message.answer(f"Ищу: {query}")
    result = wiki_search(query, sentences=3)
    await message.answer(result)
    await state.clear()
