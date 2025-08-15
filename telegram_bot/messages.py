# telegram_bot/messages.py

START = (
    "🏋️ Hi! I’m your personal AI trainer.\n"
    "Tap the button below to ask about a specific exercise."
)

ASK_BTN = "Ask question"

FILTERS_HEADER = (
    "🎯 Select filters (toggle <b>ON/OFF</b>), then send your exercise question "
    "as the next message.\n\n"
    "<b>Examples:</b>\n"
    "• How to do deadlift for back?\n"
    "• Good exercise for my biceps?\n"
)

THINKING = "⏳ Let me check…"
ERROR = "❌ Something went wrong. Please try again. {_e}"

ABOUT_PREFIX = "ℹ️ RAG service: "

ANSWER_TEMPLATE = "{answer}"

RESOURCES = (
    "<b>Resources</b>:\n"
    "{resources}"
)
