import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database


# ======================
# НАСТРОЙКИ
# ======================

BOT_TOKEN = "ТВОЙ_ТОКЕН"

ADMIN_ID = 123456789


bot = Bot(BOT_TOKEN)

dp = Dispatcher()



# ======================
# ПАМЯТЬ ДИАЛОГОВ
# ======================

active_dialogs = {}



# ======================
# СОСТОЯНИЯ
# ======================

class RequestState(StatesGroup):

    amount = State()

    photo = State()



class AdminState(StatesGroup):

    message_user = State()



# ======================
# КЛАВИАТУРЫ
# ======================

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



def admin_request_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать",
                    callback_data=f"write_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Закрыть",
                    callback_data=f"close_{user_id}"
                )
            ]
        ]
    )



def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Сбросить лимиты",
                    callback_data="reset_limits"
                )
            ]
        ]
    )



# ======================
# СТАРТ
# ======================


@dp.message(Command("start"))
async def start(message: Message):

    database.add_user(
        message.from_user.id,
        message.from_user.username
    )


    await message.answer(
        """
👋 Добро пожаловать!

Спасибо, что обратились к нам ❤️

Здесь вы можете оставить заявку на удвоение вашей голды.

Выберите действие ниже 👇
        """,
        reply_markup=main_menu()
    )



# ======================
# АДМИНКА
# ======================


@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        """
🛠 Админ панель

Выберите действие:
        """,
        reply_markup=admin_menu()
    )



# ======================
# НОВАЯ ЗАЯВКА
# ======================


@dp.callback_query(F.data=="new_request")
async def new_request(
        callback: CallbackQuery,
        state: FSMContext
):

    user_id = callback.from_user.id


    if not database.check_limit(user_id):

        await callback.message.answer(
            """
⏳ Вы уже отправляли заявку недавно ❤️

Новую заявку можно будет создать через 12 часов.

Спасибо за понимание 🙏
            """
        )

        return


    await state.set_state(
        RequestState.amount
    )


    await callback.message.answer(
        """
🔥 Отлично!

Введите количество голды или количество голды в скинах, которые хотите удвоить:

⭐ Например:
1000 голды
        """
    )


    await callback.answer()



# ======================
# ПОЛУЧЕНИЕ КОЛИЧЕСТВА
# ======================


@dp.message(RequestState.amount)
async def get_amount(
        message: Message,
        state: FSMContext
):

    await state.update_data(
        amount=message.text
    )


    await state.set_state(
        RequestState.photo
    )


    await message.answer(
        """
📸 Теперь отправьте скриншот.

На нём должна быть видна:
⭐ голда на балансе
или
⭐ скины на сумму не меньше указанной вами.

После проверки нажмите кнопку отправки заявки ❤️
        """
    )
# ======================
# ПОЛУЧЕНИЕ ФОТО
# ======================


@dp.message(RequestState.photo, F.photo)
async def get_photo(
        message: Message,
        state: FSMContext
):

    await state.update_data(
        photo=message.photo[-1].file_id
    )


    await message.answer(
        """
✅ Скриншот получен!

Проверьте всё ещё раз и нажмите кнопку ниже, чтобы отправить заявку ❤️
        """,
        reply_markup=send_request_keyboard()
    )



# ======================
# ОТПРАВКА ЗАЯВКИ
# ======================


@dp.callback_query(F.data=="send_request")
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
🎉 Ваша заявка отправлена!

Спасибо за обращение ❤️

Ожидайте проверки.
Если понадобится дополнительная информация — мы обязательно напишем.
        """
    )


    await bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""
🔥 Новая заявка #{request_id}

👤 Пользователь:
ID: {callback.from_user.id}

Username:
@{callback.from_user.username}

⭐ Количество голды:
{amount}
        """,
        reply_markup=admin_request_keyboard(
            callback.from_user.id
        )
    )


    await state.clear()

    await callback.answer()



# ======================
# АДМИН ПИШЕТ ПОЛЬЗОВАТЕЛЮ
# ======================


@dp.callback_query(F.data.startswith("write_"))
async def write_user(
        callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    active_dialogs[ADMIN_ID] = user_id


    await callback.message.answer(
        """
✍️ Напишите сообщение.

Оно будет отправлено пользователю.
        """
    )


    await callback.answer()



# ======================
# АДМИНСКИЕ СООБЩЕНИЯ
# ======================


@dp.message(
    F.from_user.id == ADMIN_ID
)
async def admin_chat(
        message: Message
):

    if ADMIN_ID not in active_dialogs:
        return


    user_id = active_dialogs[ADMIN_ID]


    await bot.send_message(
        user_id,
        f"""
💬 Сообщение от администрации:

{message.text}
        """
    )


    await message.answer(
        "✅ Отправлено"
    )



# ======================
# СООБЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЕЙ
# ======================


@dp.message()
async def user_chat(
        message: Message
):

    if message.from_user.id == ADMIN_ID:
        return


    await bot.send_message(
        ADMIN_ID,
        f"""
💬 Сообщение от пользователя:

👤 ID:
{message.from_user.id}

Username:
@{message.from_user.username}

Текст:
{message.text}
        """
    )


    active_dialogs[ADMIN_ID] = message.from_user.id



# ======================
# ЗАКРЫТИЕ
# ======================


@dp.callback_query(F.data.startswith("close_"))
async def close_user(
        callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    await bot.send_message(
        user_id,
        """
❌ Ваша заявка закрыта.

Спасибо за обращение ❤️
        """
    )


    await callback.message.answer(
        "✅ Заявка закрыта"
    )


    await callback.answer()



# ======================
# СБРОС ЛИМИТОВ
# ======================


@dp.callback_query(F.data=="reset_limits")
async def reset_limits(
        callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return


    database.reset_limits()


    await callback.message.answer(
        """
🔄 Лимиты всех пользователей сброшены.

Теперь новые заявки снова доступны.
        """
    )


    await callback.answer()



# ======================
# ЗАПУСК
# ======================


async def main():

    database.create_tables()

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
