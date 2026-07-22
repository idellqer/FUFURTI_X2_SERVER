import asyncio
import logging
import sqlite3
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
import database


logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


ADMIN_ID = config.ADMIN_ID


# ==========================
# СОСТОЯНИЯ
# ==========================

class RequestState(StatesGroup):
    waiting_amount = State()
    waiting_photo = State()


class AdminState(StatesGroup):
    waiting_message = State()


# пользователь, которому сейчас пишет админ
admin_reply = {}



# ==========================
# КЛАВИАТУРЫ
# ==========================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Новая заявка",
                    callback_data="new_request"
                )
            ]
        ]
    )



def send_request_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📨 Отправить заявку",
                    callback_data="send_request"
                )
            ]
        ]
    )



def admin_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💬 Написать пользователю",
                    callback_data=f"write_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Закрыть заявку",
                    callback_data=f"close_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔄 Сбросить лимиты",
                    callback_data="reset_limits"
                )
            ]

        ]
    )



# ==========================
# СТАРТ
# ==========================

@dp.message(Command("start"))
async def start(message: Message):

    database.add_user(
        message.from_user.id,
        message.from_user.username
    )


    await message.answer(
        """
👋 Добро пожаловать!

Здесь вы можете оставить заявку на удвоение голды.

Перед созданием заявки подготовьте:
⭐ количество голды
📸 скриншот подтверждения

Нажмите кнопку ниже, чтобы начать 👇
        """,
        reply_markup=main_menu()
    )



# ==========================
# НОВАЯ ЗАЯВКА
# ==========================

@dp.callback_query(F.data == "new_request")
async def new_request(
        callback: CallbackQuery,
        state: FSMContext
):

    user_id = callback.from_user.id


    if database.check_limit(user_id):

        await callback.message.answer(
            """
⏳ Вы уже создавали заявку недавно.

Новая заявка будет доступна через 12 часов ❤️
            """
        )

        await callback.answer()
        return



    await state.set_state(
        RequestState.waiting_amount
    )


    await callback.message.answer(
        """
🔥 Отлично, начинаем оформление!

Введите количество голды или количество голды в скинах, которые хотите удвоить:

Например:
1000 голды
        """
    )


    await callback.answer()



# ==========================
# ПОЛУЧЕНИЕ ГОЛДЫ
# ==========================

@dp.message(RequestState.waiting_amount)
async def get_amount(
        message: Message,
        state: FSMContext
):

    await state.update_data(
        amount=message.text
    )


    await state.set_state(
        RequestState.waiting_photo
    )


    await message.answer(
        """
📸 Теперь отправьте скриншот.

На нём должна быть видна:
⭐ ваша голда на балансе
или
⭐ стоимость ваших скинов

Сумма должна быть не меньше той, которую вы указали.
        """
    )



# ==========================
# ПОЛУЧЕНИЕ ФОТО
# ==========================

@dp.message(
    RequestState.waiting_photo,
    F.photo
)
async def get_photo(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()


    await state.update_data(
        photo=message.photo[-1].file_id
    )


    await message.answer(
        """
✅ Скриншот получен!

Проверьте данные и отправьте заявку.
        """,
        reply_markup=send_request_keyboard()
    )
# ==========================
# ОТПРАВКА ЗАЯВКИ
# ==========================

@dp.callback_query(F.data == "send_request")
async def send_request(
        callback: CallbackQuery,
        state: FSMContext
):

    data = await state.get_data()

    amount = data["amount"]
    photo = data["photo"]

    request_id = database.create_request(
        callback.from_user.id,
        amount,
        photo
    )


    await callback.message.answer(
        """
✅ Заявка успешно отправлена!

Ожидайте проверки ❤️

Если потребуется дополнительная информация — мы напишем вам.
        """
    )


    await bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""
🔥 Новая заявка #{request_id}

👤 Пользователь:
ID: {callback.from_user.id}
Username: @{callback.from_user.username}

⭐ Количество:
{amount}
        """,
        reply_markup=admin_keyboard(
            callback.from_user.id
        )
    )


    await state.clear()
    await callback.answer()



# ==========================
# СООБЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЯ АДМИНУ
# ==========================

@dp.message()
async def user_message(
        message: Message
):

    if message.from_user.id == ADMIN_ID:
        return


    await bot.send_message(
        ADMIN_ID,
        f"""
💬 Сообщение от пользователя:

ID:
{message.from_user.id}

Username:
@{message.from_user.username}

Текст:
{message.text}
        """
    )



# ==========================
# АДМИН НАЖАЛ НАПИСАТЬ
# ==========================

@dp.callback_query(F.data.startswith("write_"))
async def write_user(
        callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    admin_reply[callback.from_user.id] = user_id


    await callback.message.answer(
        """
✍️ Напишите сообщение пользователю.

Оно будет отправлено ему напрямую.
        """
    )


    await callback.answer()



# ==========================
# ОТПРАВКА СООБЩЕНИЯ АДМИНА
# ==========================

@dp.message()
async def admin_message(
        message: Message
):

    if message.from_user.id != ADMIN_ID:
        return


    if ADMIN_ID not in admin_reply:
        return


    user_id = admin_reply[ADMIN_ID]


    await bot.send_message(
        user_id,
        f"""
💬 Сообщение от администрации:

{message.text}
        """
    )


    await message.answer(
        "✅ Сообщение отправлено пользователю."
    )



# ==========================
# ЗАКРЫТИЕ ЗАЯВКИ
# ==========================

@dp.callback_query(F.data.startswith("close_"))
async def close_request(
        callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    await bot.send_message(
        user_id,
        """
❌ Ваша заявка была закрыта.

Спасибо за обращение ❤️
        """
    )


    await callback.message.answer(
        "✅ Заявка закрыта."
    )


    await callback.answer()



# ==========================
# СБРОС ЛИМИТОВ
# ==========================

@dp.callback_query(F.data == "reset_limits")
async def reset_limits(
        callback: CallbackQuery
):

    database.reset_limits()


    await callback.message.answer(
        """
🔄 Лимиты заявок сброшены.

Теперь пользователи снова могут отправлять заявки.
        """
    )


    await callback.answer()



# ==========================
# ЗАПУСК
# ==========================

async def main():

    await database.create_tables()

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
