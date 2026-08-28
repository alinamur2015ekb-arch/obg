import os
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from duckduckgo_search import DDGS

from state.state import pogodai, fakti, escursi, cursi

load_dotenv()

router = Router()


def ddg_search(query: str, max_results: int = 5) -> str:
    """
    Поиск через DuckDuckGo (библиотека duckduckgo_search).
    Возвращает отформатированную строку с результатами.
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)

        if not results:
            return "Ничего не найдено."

        lines = []
        for i, r in enumerate(results, start=1):
            title = r.get("title", "")
            body = r.get("body", "")
            url = r.get("href", "")

            line = f"{i}. {title}\n{body}\n🔗 {url}"
            lines.append(line)

        return "Результаты поиска:\n\n" + "\n\n".join(lines)

    except Exception as e:
        return f"⚠️ Ошибка поиска: {e}"


# Погода
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
    query = f"Погода {strana} на {srok}"

    await message.answer(f"Ищу: {query}")
    result = ddg_search(query, max_results=5)
    await message.answer(result)
    await state.clear()



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
    query = f"Популярные экскурсии в {strana} {col} вариантов"

    await message.answer(f"Ищу: {query}")
    result = ddg_search(query, max_results=5)
    await message.answer(result)
    await state.clear()


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
    query = f"Сколько {col} {valb} в {vala}"

    await message.answer(f"Ищу: {query}")
    result = ddg_search(query, max_results=5)
    await message.answer(result)
    await state.clear()
