import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
import re
import os

from config import BOT_TOKEN, ADMIN_IDS, CHAT_ID
import database

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))

# Состояния для рассылки
class BroadcastState(StatesGroup):
    waiting_for_content = State()
    waiting_for_date = State()
    waiting_for_time = State()

# --- Вспомогательные функции ---

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def send_broadcast(chat_id, content):
    """Функция отправки, вызываемая планировщиком"""
    try:
        if content['type'] == 'photo':
            await bot.send_photo(chat_id=chat_id, photo=content['file_id'], caption=content.get('text', ''))
        else:
            await bot.send_message(chat_id=chat_id, text=content['text'])
    except Exception as e:
        logging.error(f"Ошибка при рассылке: {e}")

# --- Хендлеры (Handlers) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await database.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    text = (
        "👋 Привет! Я SCN Bot.\n\n"
        "Я слежу за вашей активностью и начисляю SCN коины! 🪙\n"
        "Используйте /top чтобы увидеть рейтинг.\n\n"
        "ℹ️ Как работает SCN Bot\n\n"
        "💎 Для всех участников чата:\n"
        "• SCN коины начисляет только админ за активность в чате.\n\n"
        "🛠 Функционал для админа:\n\n"
        "1️⃣ Начислить SCN коины (ответом на сообщение участника):\n"
        "   • Форматы: +100, +300, +500, начислено 100, дать 300 и т.п.\n"
        "   • Рекомендуемые варианты: 100 / 300 / 500 SCN.\n\n"
        "2️⃣ Списать SCN коины (тоже как ответ на сообщение участника):\n"
        "   • Форматы: -100, -300, -500, снять 300, убрать 100, минус 500.\n"
    )

    if is_admin(message.from_user.id):
        text += (
            "\n"
            "3️⃣ Сброс рейтинга: команда /reset_coins — обнуляет все SCN коины у участников и топ.\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Запланировать рассылку",
                    callback_data="schedule_start",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список рассылок",
                    callback_data="list_schedules",
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "ℹ️ **Как работает SCN Bot**\n\n"
            "💎 **Для всех участников чата:**\n"
            "• SCN коины начисляет только админ за активность в чате.\n"
            "• Команда `/top` — показывает общий рейтинг по SCN коинам.\n\n"
            "🛠 **Функционал для админа (только вы это видите):**\n\n"
            "1️⃣ **Начислить SCN коины** (ответом на сообщение участника):\n"
            "   • Форматы: `+100`, `+300`, `+500`, `начислено 100`, `дать 300` и т.п.\n"
            "   • Рекомендуемые варианты: *100 / 300 / 500 SCN*.\n\n"
            "2️⃣ **Списать SCN коины** (тоже только как ответ на сообщение участника):\n"
            "   • Форматы: `-100`, `-300`, `-500`, `снять 300`, `убрать 100`, `минус 500`.\n\n"
            "3️⃣ **Рейтинг участников:**\n"
            "   • Команда `/top` — красивый топ с медальками и балансами.\n\n"
            "4️⃣ **Сброс коинов и топа:**\n"
            "   • Команда `/reset_coins` — обнуляет все SCN коины у участников, рейтинг начинается заново.\n\n"
            "5️⃣ **Отложенная рассылка в чат:**\n"
            "   • Команда `/schedule` или кнопка «Запланировать рассылку».\n"
            "   • Шаг 1: текст или фото с подписью.\n"
            "   • Шаг 2: дата по МСК — `ДД.ММ` (например `15.03`) или `ДД.ММ.ГГГГ`.\n"
            "   • Шаг 3: время по МСК — `ЧЧ:ММ` (например `14:30`).\n"
            "   • Бот отправит сообщение в чат в указанные дату и время.\n\n"
            "👇 Быстрые кнопки под сообщением /start помогут запланировать рассылку или посмотреть список."
        , parse_mode="Markdown")
    else:
        await message.answer(
            "ℹ️ SCN Bot считает активность в чате и начисляет SCN коины.\n\n"
            "💎 Доступные команды:\n"
            "• `/top` — посмотреть рейтинг участников по SCN коинам.\n"
            "• Админ может начислять и списывать SCN коины ответом на ваши сообщения.",
            parse_mode="Markdown"
        )

@dp.message(Command("reset_coins"))
async def cmd_reset_coins(message: types.Message):
    """Сброс всех SCN коинов и обнуление топа (только админ)."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return

    await database.reset_all_balances()
    await message.answer(
        "🔄 **Сброс выполнен!**\n\n"
        "💎 Все SCN коины обнулены, таблица участников очищена.\n"
        "🏆 Рейтинг (/top) пустой — участники появятся снова, когда админ начислит им коины. ✨",
        parse_mode="Markdown"
    )

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    top_users = await database.get_top_users(15)
    
    header = "🏆 **ТОП УЧАСТНИКОВ SCN** 🏆\n\n"
    if not top_users:
        await message.answer(header + "Пока список пуст. Начинайте общаться! 🚀", parse_mode="Markdown")
        return

    text = header
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(top_users):
        user_id, full_name, balance, username = user
        
        # Форматирование имени (если есть юзернейм, добавляем ссылку)
        display_name = full_name
        
        # Медаль или место
        rank = medals[i] if i < 3 else f"**{i+1}.**"
        
        text += f"{rank} {display_name}: *{balance} SCN* 💎\n"
    
    text += "\n_Общайтесь и получайте коины от админа!_"
    await message.answer(text, parse_mode="Markdown")

# Хендлер начисления баллов (Reply + Admin Check)
@dp.message(F.reply_to_message)
async def admin_manage_points(message: types.Message):
    # Проверка на админа
    if not is_admin(message.from_user.id):
        return

    # Пропускаем, если ответ самому себе (опционально)
    if message.reply_to_message.from_user.id == message.from_user.id:
        # Можно разрешить админу начислять себе для теста
        pass

    text = message.text.lower()
    amount = 0
    action = ""

    # Ищем числа в сообщении
    # Поддерживаем форматы: "+100", "начислено 100", "100 баллов", "снять 500"
    
    # 1. Сначала проверяем явные команды добавления
    add_match = re.search(r'(?:\+|начислено|дать|плюс)\s*(\d+)', text)
    
    # 2. Проверяем явные команды удаления
    remove_match = re.search(r'(?:-|снять|убрать|минус)\s*(\d+)', text)
    
    # 3. Если просто число "100", считаем это начислением (опционально, но опасно, лучше строго)
    # Оставим только явные команды для безопасности
    
    if add_match:
        amount = int(add_match.group(1))
        action = "add"
    elif remove_match:
        amount = int(remove_match.group(1))
        action = "remove"
    else:
        return # Не распознано как команда баллов

    target_user = message.reply_to_message.from_user
    
    if target_user.is_bot:
        await message.answer("🤖 Ботам баллы не положены.")
        return

    # Логика обновления
    final_amount = amount if action == "add" else -amount
    
    # Сначала убедимся, что юзер есть в базе
    await database.add_user(target_user.id, target_user.username, target_user.full_name)
    
    # Обновляем
    new_balance = await database.update_balance(target_user.id, final_amount)
    
    # Красивый ответ
    if action == "add":
        await message.reply(
            f"✅ **Успешно!**\n"
            f"Пользователю {target_user.full_name} начислено *{amount} SCN*!\n"
            f"💰 Текущий баланс: *{new_balance} SCN*",
            parse_mode="Markdown"
        )
    else:
        await message.reply(
            f"🔻 **Списание!**\n"
            f"У пользователя {target_user.full_name} списано *{amount} SCN*.\n"
            f"💰 Текущий баланс: *{new_balance} SCN*",
            parse_mode="Markdown"
        )

# --- FSM для рассылки (Schedule) ---

@dp.message(Command("schedule"))
async def cmd_schedule(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    await message.answer(
        "📢 **Создание рассылки**\n\n"
        "Отправьте сообщение, которое нужно разослать.\n"
        "Это может быть просто текст или фото с подписью.",
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastState.waiting_for_content)

@dp.message(BroadcastState.waiting_for_content)
async def process_schedule_content(message: types.Message, state: FSMContext):
    content = {}
    
    if message.photo:
        content['type'] = 'photo'
        content['file_id'] = message.photo[-1].file_id
        content['text'] = message.caption if message.caption else ""
    elif message.text:
        content['type'] = 'text'
        content['text'] = message.text
    else:
        await message.answer("Пожалуйста, отправьте текст или фото.")
        return

    await state.update_data(content=content)

    await message.answer(
        "📅 **Укажите дату отправки (по Москве)**\n"
        "Формат: `ДД.ММ` (например `15.03` или `25.12`).",
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastState.waiting_for_date)


@dp.message(BroadcastState.waiting_for_date)
async def process_schedule_date(message: types.Message, state: FSMContext):
    raw = message.text.strip()
    msk_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(msk_tz)

    # ДД.ММ или ДД.ММ.ГГГГ
    if re.match(r'^\d{1,2}\.\d{1,2}$', raw):
        day, month = map(int, raw.split('.'))
        year = now.year
    elif re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', raw):
        day, month, year = map(int, raw.split('.'))
    else:
        await message.answer("❌ Неверный формат даты. Используйте `ДД.ММ` (например `15.03`) или `ДД.ММ.ГГГГ`.")
        return

    try:
        run_date = msk_tz.localize(datetime(year, month, day))
        if run_date.date() < now.date():
            await message.answer("❌ Эта дата уже в прошлом. Укажите сегодняшний день или будущую дату.")
            return
    except ValueError:
        await message.answer("❌ Некорректная дата (проверьте число и месяц).")
        return

    await state.update_data(schedule_date=run_date)
    await message.answer(
        "🕒 **Укажите время отправки (по Москве)**\n"
        "Формат: `ЧЧ:ММ` (например `14:30` или `18:00`).",
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastState.waiting_for_time)


@dp.message(BroadcastState.waiting_for_time)
async def process_schedule_time(message: types.Message, state: FSMContext):
    time_str = message.text.strip()

    if not re.match(r'^\d{1,2}:\d{2}$', time_str):
        await message.answer("❌ Неверный формат. Используйте `ЧЧ:ММ`, например `15:00`.")
        return

    try:
        hours, minutes = map(int, time_str.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("invalid time")
    except ValueError:
        await message.answer("❌ Некорректное время. Часы 0–23, минуты 0–59.")
        return

    data = await state.get_data()
    content = data['content']
    schedule_date = data.get('schedule_date')  # datetime в МСК
    msk_tz = pytz.timezone('Europe/Moscow')

    run_date = schedule_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    now = datetime.now(msk_tz)
    if run_date <= now:
        await message.answer("❌ Указанные дата и время уже в прошлом. Начните заново: /schedule или кнопка «Запланировать рассылку».")
        await state.clear()
        return

    target_chat_id = CHAT_ID
    scheduler.add_job(
        send_broadcast,
        'date',
        run_date=run_date,
        args=[target_chat_id, content]
    )

    await message.answer(
        f"✅ **Рассылка запланирована!**\n\n"
        f"📅 Дата: {run_date.strftime('%d.%m.%Y')}\n"
        f"🕒 Время: {run_date.strftime('%H:%M')} (МСК)\n"
        f"📩 Тип: {'Фото + Текст' if content['type'] == 'photo' else 'Текст'}",
        parse_mode="Markdown"
    )
    await state.clear()


# --- Callbacks for inline buttons ---

@dp.callback_query(F.data == "schedule_start")
async def cb_schedule_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Только админ может создавать рассылки.", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(
        "📢 **Создание рассылки**\n\n"
        "Отправьте сообщение, которое нужно разослать.\n"
        "Это может быть просто текст или фото с подписью.",
        parse_mode="Markdown",
    )
    await state.set_state(BroadcastState.waiting_for_content)


@dp.callback_query(F.data == "list_schedules")
async def cb_list_schedules(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Только админ может смотреть список рассылок.", show_alert=True)
        return

    await callback.answer()

    jobs = scheduler.get_jobs()
    if not jobs:
        await callback.message.answer("📭 Сейчас нет запланированных рассылок.")
        return

    tz = pytz.timezone("Europe/Moscow")
    lines = ["📋 **Список запланированных рассылок (по МСК):**\n"]
    buttons = []

    for idx, job in enumerate(jobs, start=1):
        # Ожидаем, что args = [chat_id, content_dict]
        content = job.args[1] if len(job.args) > 1 else {}
        text = content.get("text", "") or "(без текста)"
        if len(text) > 60:
            text = text[:57] + "..."

        icon = "🖼" if content.get("type") == "photo" else "💬"
        run_time = job.next_run_time.astimezone(tz) if job.next_run_time else None
        time_str = run_time.strftime("%d.%m %H:%M") if run_time else "время не задано"

        lines.append(f"{idx}. {icon} {time_str} — {text}")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Удалить #{idx} ({time_str})",
                    callback_data=f"del_job:{job.id}",
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("\n".join(lines), reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("del_job:"))
async def cb_delete_job(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Только админ может удалять рассылки.", show_alert=True)
        return

    job_id = callback.data.split(":", 1)[1]
    try:
        scheduler.remove_job(job_id)
        await callback.answer("Рассылка удалена ✅", show_alert=False)
    except Exception:
        await callback.answer("Рассылка уже не найдена.", show_alert=True)

# --- Запуск ---

async def on_startup(bot: Bot):
    await database.create_table()
    scheduler.start()
    print("Bot is running...")

async def main():
    dp.startup.register(on_startup)
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")
