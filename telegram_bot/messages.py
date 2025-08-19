# telegram_bot/messages.py

START = (
    "Hey, {username}! I’m GymWiseAI 🏋️‍♂️\n"
    "I explain exercises clearly and safely.\n\n"
    "Try /ask_question to:\n"
    "• Pick filters (e.g., Muscle Group, Equipment)\n"
    "• Ask your question (e.g., “How to correctly do pullups?”)\n\n"
    "What I’ll return:\n"
    "• Quick answer + list of resources that might help\n"
    "• Step-by-step setup & cues\n"
    "• Easier/harder variations\n\n"
    "<b style='color:red;'>TIP:</b> The more specific your question and filters, the better the answer."
)

ASK_BTN = "Ask question"

FILTERS_HEADER = (
    "🎯 Select filters (toggle <b>ON/OFF</b>), then send your exercise question "
    "as the next message.\n\n"
    "<b>Examples:</b>\n"
    "• How to do deadlift for back?\n"
    "• Good exercise to hit my biceps?\n"
)

THINKING = "⏳ Let me check…"
ERROR = "❌ Something went wrong. Please try again. {_e}"

ABOUT_PREFIX = "ℹ️ Service: "

ANSWER_TEMPLATE = "{answer}"

RESOURCES = (
    "<b>Jefit exersices that might fit your question:</b>:\n"
    "{resources}"
)
