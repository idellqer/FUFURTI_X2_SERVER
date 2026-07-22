import asyncio
from aiogram import Bot,Dispatcher,types,F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
from config import BOT_TOKEN,ADMIN_ID
from database import add_request

bot=Bot(BOT_TOKEN)
def admin_keyboard(uid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accept_{uid}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{uid}"
                )
            ]
        ]
    )
dp=Dispatcher()
data={}

@dp.message(Command("start"))
async def start(m:types.Message):
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Новая заявка",callback_data="new")]])
    await m.answer("FUFURTI X2\nСоздайте заявку",reply_markup=kb)

@dp.callback_query(F.data=="new")
async def new(c):
    data[c.from_user.id]={}
    await c.message.answer("Введите количество голды или стоимость скинов:")

@dp.message(F.text)
async def text(m):
    if m.from_user.id in data and "amount" not in data[m.from_user.id]:
        data[m.from_user.id]["amount"]=m.text
        await m.answer("Отправьте скриншот")

@dp.message(F.photo)
async def photo(m):
    uid=m.from_user.id
    if uid in data:
        add_request(uid,data[uid]["amount"],m.photo[-1].file_id)
        await m.answer("Заявка отправлена на проверку")
        await bot.send_photo(
    ADMIN_ID,
    m.photo[-1].file_id,
    caption=f"📩 Новая заявка\n\n👤 ID: {uid}\n💰 Сумма: {data[uid]['amount']}",
    reply_markup=admin_keyboard(uid)
)

async def main():
    await dp.start_polling(bot)
@dp.callback_query()
async def admin_action(c):
    action, uid = c.data.split("_")

    if action == "accept":
        await bot.send_message(
            int(uid),
            "✅ Ваша заявка принята!"
        )

        await c.message.edit_caption(
            caption=c.message.caption + "\n\n✅ ПРИНЯТО"
        )

    elif action == "reject":
        await bot.send_message(
            int(uid),
            "❌ Ваша заявка отклонена."
        )

        await c.message.edit_caption(
            caption=c.message.caption + "\n\n❌ ОТКЛОНЕНО"
        )

    await c.answer()
asyncio.run(main())
