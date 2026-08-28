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


# ---------------------------
# Поиск через Wikipedia
# ---------------------------
def wiki_search(query: str, sentences: int = 3) -> str:
    """
    Поиск через Wikipedia API.
    Возвращает отформатированную строку с результатами.
    """
    try:
        # Поиск по запросу
        search_results = wikipedia.search(query, results=5)

        if not search_results:
            return "Ничего не найдено."

        lines = []
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summary = page.summary[:500]  # Первые 500 символов
                url = page.url

                line = f"📖 {title}\n{summary}...\n🔗 {url}"
                lines.append(line)
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                # Пропускаем страницы неоднозначности и ошибки
                continue
            except JSONDecodeError as e:
                logger.warning(f"JSONDecodeError для {title}: {e}")
                continue

        if not lines:
            return "Ничего не найдено."

        return "Результаты из Wikipedia:\n\n" + "\n\n".join(lines[:5])

    except JSONDecodeError as e:
        logger.error(f"JSONDecodeError при поиске '{query}': {e}")
        return "⚠️ Ошибка формата ответа от Wikipedia. Попробуй другой запрос."
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {e}")
        return "⚠️ Ошибка сети. Проверь подключение к интернету."
    except Exception as e:
        logger.error(f"Ошибка поиска: {type(e).__name__}: {e}")
        return f"⚠️ Ошибка поиска: {type(e).__name__}: {e}"


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
