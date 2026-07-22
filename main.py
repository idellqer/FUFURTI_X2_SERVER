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
            # =====================
# ПОЛУЧЕНИЕ ФОТО
# =====================


@dp.message(F.photo)
async def photo(message: Message):

    uid = message.from_user.id


    if uid in user_state:

        if user_state[uid]["step"]=="photo":

            user_state[uid]["photo"] = message.photo[-1].file_id
            user_state[uid]["step"]="confirm"


            kb = InlineKeyboardMarkup(
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
                "Фото получено.\n\n"
                "Проверьте данные и нажмите отправить заявку.",
                reply_markup=kb
            )



# =====================
# ОТПРАВКА ЗАЯВКИ
# =====================


@dp.callback_query(F.data=="send_request")
async def send_request(callback: CallbackQuery):

    uid = callback.from_user.id


    if uid not in user_state:
        return


    data = user_state[uid]


    req_id = database.create_request(
        uid,
        data["amount"],
        data["photo"]
    )


    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать пользователю",
                    callback_data=f"chat_{uid}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Закрыть заявку",
                    callback_data=f"close_{req_id}"
                )
            ]
        ]
    )


    await bot.send_photo(
        ADMIN_ID,
        data["photo"],
        caption=
        f"📩 Новая заявка #{req_id}\n\n"
        f"👤 Пользователь: {uid}\n"
        f"💰 Количество: {data['amount']}",
        reply_markup=admin_kb
    )


    await callback.message.answer(
        "✅ Заявка отправлена.\n"
        "Ожидайте проверки."
    )


    del user_state[uid]



# =====================
# АДМИН ЗАКРЫВАЕТ
# =====================


@dp.callback_query(F.data.startswith("close_"))
async def close(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return


    req_id = int(
        callback.data.split("_")[1]
    )


    req = database.get_request(req_id)


    if req:

        database.close_request(req_id)


        await bot.send_message(
            req[1],
            "❌ Ваша заявка закрыта."
        )


        await callback.message.answer(
            "Заявка закрыта."
        )



# =====================
# ЗАПУСК
# =====================


async def main():

    await dp.start_polling(bot)



if __name__=="__main__":
    asyncio.run(main())
