import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command, CommandStart

from config import BOT_TOKEN, ADMIN_ID
import database


bot = Bot(BOT_TOKEN)

dp = Dispatcher()


# временное хранение шагов пользователей
user_state = {}

# активный чат админа
admin_chat = {}



# =====================
# КЛАВИАТУРЫ
# =====================


def main_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Новая заявка")
            ],
            [
                KeyboardButton(text="📄 Моя заявка")
            ]
        ],
        resize_keyboard=True
    )



def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Заявки",
                    callback_data="requests"
                )
            ]
        ]
    )



# =====================
# СТАРТ
# =====================


@dp.message(CommandStart())
async def start(message: Message):

    database.add_user(
        message.from_user.id,
        message.from_user.username
    )


    await message.answer(
        "👋 Добро пожаловать в FUFURTI X2\n\n"
        "Выберите действие:",
        reply_markup=main_menu()
    )


# =====================
# НОВАЯ ЗАЯВКА
# =====================


@dp.message(F.text=="🟢 Новая заявка")
async def new_request(message: Message):

    user_state[message.from_user.id] = {
        "step":"amount"
    }


    await message.answer(
        "Введите количество голды или стоимость скинов:"
    )



# =====================
# ВВОД ГОЛДЫ
# =====================


@dp.message(F.text)
async def amount(message: Message):

    uid = message.from_user.id


    if uid in user_state:

        if user_state[uid]["step"]=="amount":

            user_state[uid]["amount"] = message.text
            user_state[uid]["step"]="photo"


            await message.answer(
                "Теперь отправьте скриншот.\n\n"
                "На нём должна быть видна голда "
                "или скины стоимостью не меньше указанного количества."
            )

            return
