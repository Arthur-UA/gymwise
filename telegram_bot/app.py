import os
import asyncio
import logging
import sys
from typing import Dict, List

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import httpx
import json

from telegram_bot import messages as msg

# -------------------- ENV --------------------
load_dotenv(override=True)
TOKEN = os.environ["BOT_API_KEY"]
RAG_API_BASE_URL = os.environ.get("RAG_API_BASE_URL", "http://localhost:8000").rstrip("/")

# Comma-separated options (you can change freely)
# e.g. EQUIPMENT_OPTIONS="barbell,dumbbell,kettlebell,bodyweight,machine"
#      MUSCLE_OPTIONS="chest,back,legs,glutes,shoulders,arms,core"
EQUIPMENT_OPTIONS: List[str] = [s.strip() for s in os.environ.get("EQUIPMENT_OPTIONS").split(",") if s.strip()]
MUSCLE_OPTIONS: List[str] = [s.strip() for s in os.environ.get("MUSCLE_OPTIONS").split(",") if s.strip()]

# -------------------- BOT CORE --------------------
dp = Dispatcher()
_http: httpx.AsyncClient | None = None

class AskFlow(StatesGroup):
    choosing_filters = State()   # toggling equipment/muscle
    awaiting_question = State()  # next user message is the question

# Helpers to manage filters in FSM
EMPTY_FILTERS = {
    "Equipment": {opt: False for opt in EQUIPMENT_OPTIONS},
    "Muscle Group": {opt: False for opt in MUSCLE_OPTIONS},
}

def build_filters_kb(filters: Dict[str, Dict[str, bool]]) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard with toggle buttons for Equipment and Muscle Group.
    ON -> ✅ name, OFF -> ◻️ name
    callback data: flt|group|value
    """
    kb = InlineKeyboardBuilder()

    def add_section(title: str, items: Dict[str, bool]):
        # Section title (disabled label)
        kb.row(InlineKeyboardButton(text=f"— {title} —", callback_data="noop"), width=1)
        row: List[InlineKeyboardButton] = []
        for name, on in items.items():
            label = f"{'✅' if on else '◻️'} {name}"
            row.append(InlineKeyboardButton(text=label, callback_data=f"flt|{title}|{name}"))
            if len(row) == 2:  # 2 columns for compactness
                kb.row(*row)
                row = []
        if row:
            kb.row(*row)

    add_section("Equipment", filters["Equipment"])
    add_section("Muscle Group", filters["Muscle Group"])
    return kb.as_markup()

def active_filters(filters: Dict[str, Dict[str, bool]]) -> Dict[str, List[str]]:
    """Return only toggled values."""
    result: Dict[str, List[str]] = {}
    for group, items in filters.items():
        on_vals = [k for k, v in items.items() if v]
        if on_vals:
            # Normalize keys to API expected names
            if group == "Muscle Group":
                key = "muscleGroup"
            elif group == "Equipment":
                key = "equipment"
            else:
                key = group
            result[key] = on_vals
    return result

# -------------------- HANDLERS --------------------
@dp.message(CommandStart())
async def on_start(message: Message):
    """Brief bot description and the one button that SENDS the /ask_question command"""
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/ask_question")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(msg.START.format(username=message.from_user.first_name), reply_markup=kb)


@dp.message(Command("about"))
async def on_about(message: Message):
    try:
        r = await _http.get(f"{RAG_API_BASE_URL}/")
        r.raise_for_status()
        await message.answer(msg.ABOUT_PREFIX + r.text)
    except Exception:
        await message.answer(msg.ERROR)


@dp.message(Command("ask_question"))
async def on_ask_question(message: Message, state: FSMContext):
    # Initialize filters in state
    await state.set_state(AskFlow.choosing_filters)
    await state.update_data(filters=json.loads(json.dumps(EMPTY_FILTERS)))  # deep copy

    data = await state.get_data()
    filters = data["filters"]
    kb = build_filters_kb(filters)

    await message.answer(msg.FILTERS_HEADER, reply_markup=kb, parse_mode="HTML")
    await state.set_state(AskFlow.awaiting_question)


@dp.callback_query(F.data.startswith("flt|"))
async def on_toggle_filter(cb: CallbackQuery, state: FSMContext):
    """Toggle a filter and refresh the keyboard."""
    try:
        _, group, name = cb.data.split("|", 2)
        data = await state.get_data()
        filters = data.get("filters")
        if not filters or group not in filters or name not in filters[group]:
            await cb.answer("Unknown filter", show_alert=False)
            return

        filters[group][name] = not filters[group][name]
        await state.update_data(filters=filters)
        await cb.message.edit_reply_markup(reply_markup=build_filters_kb(filters))
        await cb.answer("Toggled")
    except Exception:
        await cb.answer("Error", show_alert=False)


@dp.callback_query(F.data == "noop")
async def on_noop(cb: CallbackQuery):
    """Make non-clickable labels in inline keyboards not produce errors."""
    await cb.answer(cache_time=60)

@dp.message(AskFlow.awaiting_question, F.text)
async def on_question(message: Message, state: FSMContext):
    data = await state.get_data()
    filters_state = data.get("filters")

    filters = active_filters(filters_state)

    # Show typing while we call API
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        payload = {"question_text": message.text.strip(), "filters": filters}

        r = await _http.post(f"{RAG_API_BASE_URL}/ask_excercise_question", json=payload, timeout=60.0)
        r.raise_for_status()

        data = r.json()["response"]
        answer = data["answer"]
        urls = [resource["metadata"]["url"] for resource in data["context"]]
        resources = "\n".join(urls)

        await message.answer(
            msg.ANSWER_TEMPLATE.format(answer=answer, urls=urls),
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            msg.RESOURCES.format(resources=resources),
            parse_mode=ParseMode.HTML
        )
    except Exception as _e:
        await message.answer(msg.ERROR.format(_e=_e))

    await state.clear()

@dp.message(F.text)
async def default_echo(message: Message):
    await message.answer(
        "Use /ask_question to choose filters, then send your exercise question."
    )

async def main() -> None:
    global _http
    _http = httpx.AsyncClient(timeout=30.0)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.start_polling(bot)
    finally:
        await _http.aclose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
