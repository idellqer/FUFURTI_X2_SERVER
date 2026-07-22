import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
import database


bot = Bot(config.BOT_TOKEN)
dp = Dispatcher()


# =========================
# СОСТОЯНИЯ
# =========================

class RequestState(StatesGroup):
    waiting_amount = State()
    waiting_photo = State()


class ChatState(StatesGroup):
    waiting_message = State()


# =========================
# МЕНЮ
# =========================

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


# =========================
# СТАРТ
# =========================

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

Перед отправкой заявки внимательно подготовьте скриншот вашего аккаунта ❤️

Выберите действие ниже 👇
        """,
        reply_markup=main_menu()
    )


# =========================
# НОВАЯ ЗАЯВКА
# =========================

@dp.callback_query(F.data == "new_request")
async def new_request(
        callback: CallbackQuery,
        state: FSMContext
):

    user_id = callback.from_user.id


    if not database.check_limit(user_id):

        await callback.message.answer(
            """
⏳ Вы уже отправляли заявку недавно ❤️

Повторная отправка будет доступна через 12 часов.

Спасибо за понимание 🙏
            """
        )

        return


    await state.set_state(RequestState.waiting_amount)


    await callback.message.answer(
        """
🔥 Отлично, начинаем оформление заявки!

Введите количество голды или количество голды в скинах, которые хотите удвоить:

Например:
500 голды
или
1200 голды в скинах
        """
    )


# =========================
# ПОЛУЧЕНИЕ КОЛИЧЕСТВА
# =========================

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
📸 Отлично!

Теперь отправьте скриншот, где видно:

✅ количество голды на балансе
или
✅ ваши скины, стоимость которых не меньше указанного количества.

После отправки появится кнопка подтверждения ❤️
        """
    )


# =========================
# ПОЛУЧЕНИЕ ФОТО
# =========================

@dp.message(
    RequestState.waiting_photo,
    F.photo
)
async def get_photo(
        message: Message,
        state: FSMContext
):

    await state.update_data(
        photo=message.photo[-1].file_id
    )


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📨 Отправить заявку",
                    callback_data="send_request"
                )
            ]
        ]
    )


    await message.answer(
        """
✅ Скриншот получен!

Проверьте данные и нажмите кнопку ниже, чтобы отправить заявку.
        """,
        reply_markup=keyboard
    )
# =========================
# ОТПРАВКА ЗАЯВКИ
# =========================

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


    database.set_limit(
        callback.from_user.id
    )


    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать пользователю",
                    callback_data=f"chat_{callback.from_user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Закрыть заявку",
                    callback_data=f"close_{request_id}"
                )
            ]
        ]
    )


    await bot.send_photo(
        config.ADMIN_ID,
        photo,
        caption=f"""
📩 Новая заявка #{request_id}

👤 Пользователь:
@{callback.from_user.username}

🪙 Количество:
{amount}

Проверьте заявку 👇
        """,
        reply_markup=admin_keyboard
    )


    await callback.message.answer(
        """
✅ Ваша заявка успешно отправлена!

Администратор проверит её и свяжется с вами ❤️

Спасибо за ожидание 🙏
        """
    )


    await state.clear()



# =========================
# ЗАКРЫТИЕ ЗАЯВКИ
# =========================

@dp.callback_query(F.data.startswith("close_"))
async def close_request(
        callback: CallbackQuery
):

    if callback.from_user.id != config.ADMIN_ID:
        return


    request_id = int(
        callback.data.split("_")[1]
    )


    database.close_request(request_id)


    await callback.message.answer(
        """
❌ Заявка закрыта.

Пользователь получил уведомление.
        """
    )



# =========================
# НАЧАТЬ ОБЩЕНИЕ
# =========================

@dp.callback_query(F.data.startswith("chat_"))
async def start_chat(
        callback: CallbackQuery,
        state: FSMContext
):

    if callback.from_user.id != config.ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[1]
    )


    await state.update_data(
        chat_user=user_id
    )


    await state.set_state(
        ChatState.waiting_message
    )


    await callback.message.answer(
        """
💬 Напишите сообщение пользователю.

Оно будет отправлено ему прямо в боте.
        """
    )



# =========================
# ОТПРАВКА СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЮ
# =========================

@dp.message(ChatState.waiting_message)
async def send_chat_message(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()

    user_id = data["chat_user"]


    await bot.send_message(
        user_id,
        f"""
💬 Сообщение от администратора:

{message.text}
        """
    )


    await message.answer(
        """
✅ Сообщение отправлено пользователю.
        """
    )


    await state.clear()



# =========================
# СБРОС ЛИМИТОВ
# =========================

@dp.message(Command("reset"))
async def reset_limits(
        message: Message
):

    if message.from_user.id != config.ADMIN_ID:
        return


    database.reset_limits()


    await message.answer(
        """
🔄 Лимиты всех пользователей сброшены.

Теперь все снова могут отправлять заявки.
        """
    )



# =========================
# ЗАПУСК
# =========================

async def main():

    await database.create_tables()

    print("Bot started")


    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
