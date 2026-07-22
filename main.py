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

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database
import config


closed_users = set()
bot = Bot(token=config.BOT_TOKEN)

dp = Dispatcher()


# =====================
# СОСТОЯНИЯ
# =====================

class RequestState(StatesGroup):
    waiting_amount = State()
    waiting_photo = State()


class AdminChatState(StatesGroup):
    chatting = State()



# =====================
# КНОПКИ
# =====================

def main_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✨ Новая заявка")
            ],
            [
                KeyboardButton(text="📋 Моя заявка")
            ],
            [
                KeyboardButton(text="ℹ️ Помощь")
            ]
        ],
        resize_keyboard=True
    )


def admin_buttons(request_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать пользователю",
                    callback_data=f"chat_{request_id}"
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



# =====================
# START
# =====================

@dp.message(Command("start"))
async def start(message: Message):

    database.add_user(
        message.from_user.id,
        message.from_user.username or "без username"
    )


    await message.answer(
        """
👋 Добро пожаловать!

Рады видеть вас здесь ❤️

В этом боте вы можете оформить заявку на удвоение вашей голды или стоимости ваших скинов.

Перед отправкой заявки подготовьте скриншот, где хорошо видно вашу голду или ваши скины.

Выберите действие ниже 👇
        """,
        reply_markup=main_menu()
    )



# =====================
# НОВАЯ ЗАЯВКА
# =====================

@dp.message(F.text == "✨ Новая заявка")
async def new_request(message: Message, state: FSMContext):

    await state.set_state(RequestState.waiting_amount)


    await message.answer(
        """
🔥 Отлично, начнём оформление заявки!

Введите количество голды или стоимость скинов, которые хотите удвоить:

Например:
• 500 голды
• 1500 голды в скинах

Введите значение ниже 👇
        """
    )



@dp.message(RequestState.waiting_amount)
async def get_amount(message: Message, state: FSMContext):

    await state.update_data(
        amount=message.text
    )


    await state.set_state(RequestState.waiting_photo)


    await message.answer(
        """
📸 Отлично!

Теперь отправьте скриншот, где видно:

✅ вашу голду на балансе
или
✅ ваши скины и их стоимость в голде

Пожалуйста, убедитесь, что изображение хорошо читается ❤️
        """
    )



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
        f"""
✅ Скриншот получен!

Проверьте данные:

💎 Количество:
{data['amount']}

Если всё правильно — отправьте заявку 👇
        """,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📨 Отправить заявку",
                        callback_data="send_request"
                    )
                ]
            ]
        )
    )
# =====================
# ОТПРАВКА ЗАЯВКИ
# =====================

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
🎉 Ваша заявка успешно отправлена!

Спасибо за ожидание ❤️

Заявка уже передана на проверку.

Если понадобится дополнительная информация — мы свяжемся с вами здесь.
        """
    )


    await bot.send_photo(
        chat_id=config.ADMIN_ID,
        photo=photo,
        caption=f"""
🔔 Новая заявка №{request_id}

👤 Пользователь:
@{callback.from_user.username or "без username"}

🆔 ID:
{callback.from_user.id}

💎 Количество:
{amount}

Статус:
⏳ Ожидает проверки
        """,
        reply_markup=admin_buttons(request_id)
    )


    await state.clear()

    await callback.answer()



# =====================
# АДМИН: НАПИСАТЬ ПОЛЬЗОВАТЕЛЮ
# =====================

admin_chats = {}



@dp.callback_query(F.data.startswith("chat_"))
async def start_admin_chat(
        callback: CallbackQuery,
        state: FSMContext
):

    request_id = int(
        callback.data.split("_")[1]
    )


    request = database.get_request(
        request_id
    )


    if not request:
        await callback.answer(
            "Заявка не найдена"
        )
        return


    user_id = request[1]


    admin_chats[callback.from_user.id] = user_id


    await state.set_state(
        AdminChatState.chatting
    )


    await callback.message.answer(
        f"""
💬 Вы вошли в диалог с пользователем.

Теперь все ваши сообщения будут отправляться ему.

Чтобы закончить диалог:
напишите /end
        """
    )


    await callback.answer()



# =====================
# АДМИН ПИШЕТ ПОЛЬЗОВАТЕЛЮ
# =====================

@dp.message(AdminChatState.chatting)
async def admin_message(
        message: Message,
        state: FSMContext
):

    if message.text == "/end":

        admin_chats.pop(
            message.from_user.id,
            None
        )

        await state.clear()

        await message.answer(
            "🔙 Диалог завершён"
        )

        return



    user_id = admin_chats.get(
        message.from_user.id
    )


    if not user_id:
        await message.answer(
            "Пользователь не выбран"
        )
        return



    database.save_message(
        user_id,
        "admin",
        message.text
    )


    await bot.send_message(
        user_id,
        f"""
💬 Сообщение от поддержки:

{message.text}
        """
    )



# =====================
# ПОЛЬЗОВАТЕЛЬ ОТВЕЧАЕТ
# =====================

@dp.message()
async def user_reply(message: Message):

    if message.from_user.id == config.ADMIN_ID:
        return


    # ищем активный диалог

    for admin_id, user_id in admin_chats.items():

        if user_id == message.from_user.id:

            database.save_message(
                user_id,
                "user",
                message.text
            )


            await bot.send_message(
                admin_id,
                f"""
👤 Ответ пользователя:

@{message.from_user.username or "без username"}

{message.text}
                """
            )

            return



# =====================
# ЗАКРЫТИЕ ЗАЯВКИ
# =====================

@dp.callback_query(F.data.startswith("close_"))
async def close(
        callback: CallbackQuery
):

    request_id = int(
        callback.data.split("_")[1]
    )


    request = database.get_request(
        request_id
    )


    if request:

        user_id = request[1]
        
        closed_users.add(user_id)

        database.close_request(
            request_id
        )


        await bot.send_message(
            user_id,
            """
❌ Ваша заявка была закрыта.

Спасибо за обращение ❤️

Если понадобится помощь — вы можете создать новую заявку.
            """
        )


    await callback.message.answer(
        "✅ Заявка закрыта"
    )


    await callback.answer()



# =====================
# ЗАПУСК
# =====================

async def main():

    database.create_tables()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    print("BOT STARTED")

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
