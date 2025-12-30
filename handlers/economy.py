from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from datetime import datetime, timedelta
import random
import asyncio
from database import Database
from config import *

async def cmd_kopat_torf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /kopat_torf"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Создаем пользователя если не существует
    db.create_user(user_id, username, first_name)
    user = db.get_user(user_id)
    
    # Проверка на перфорацию
    if user['perforation_count'] > 0:
        await update.message.reply_text("🩸 Вы на лечении в суглинках! Добыча невозможна.")
        return
    
    # Пассивный доход
    now = datetime.now()
    last_income = datetime.fromisoformat(user['last_passive_income'])
    
    if (now - last_income).total_seconds() < 3600:
        wait_time = 3600 - (now - last_income).total_seconds()
        minutes = int((wait_time % 3600) // 60)
        await update.message.reply_text(f"⏳ Торф ещё копится! Ждите {minutes} минут.")
        return
    
    # Расчет дохода
    base_income = TRF_PER_HOUR
    chat_data = db.get_chat(update.effective_chat.id)
    
    # Модификатор от pH
    ph_modifier = 1.0
    if chat_data['ph_level'] < 5.0:
        ph_modifier = 0.7  # Кислая почва - меньше дохода
    elif chat_data['ph_level'] > 6.5:
        ph_modifier = 1.3  # Нейтральная - больше дохода
    
    income = int(base_income * ph_modifier)
    
    # Добавляем доход
    new_trf = db.add_trf(user_id, income)
    db.update_user(user_id, last_passive_income=now.isoformat())
    
    # Запись в историю
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO mining (user_id, action, amount) VALUES (?, ?, ?)',
                   (user_id, 'passive_income', income))
        conn.commit()
    
    await update.message.reply_text(
        f"⛏️ Добыто: {income} TRF\n"
        f"📊 pH модификатор: x{ph_modifier:.1f}\n"
        f"💰 Новый баланс: {new_trf} TRF\n"
        f"⏳ Следующая добыча через час"
    )

async def cmd_torforazvedka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /torforazvedka"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['trf'] < 10:
        await update.message.reply_text("❌ Нужно минимум 10 TRF для разведки!")
        return
    
    # Случайный исход
    rand = random.random()
    found = 0
    loss = 0
    
    if rand < CHANCE_CO2:
        # Выброс CO₂
        loss = random.randint(10, 50)
        new_trf = max(0, user['trf'] - loss)
        db.update_user(user_id, trf=new_trf)
        
        # Активируем опасность CO2 в чате
        chat_id = update.effective_chat.id
        db.update_chat(chat_id, co2_active=True, last_danger=datetime.now().isoformat())
        
        await update.message.reply_text(
            f"💨 ВЫБРОС CO₂!\n"
            f"Потеряно: {loss} TRF\n"
            f"⚠️ В чате активирована опасность CO₂!\n"
            f"💰 Осталось: {new_trf} TRF"
        )
        outcome = "co2"
        
    elif rand < CHANCE_CO2 + CHANCE_GOLD_VEIN:
        # Золотая жила
        bonus = random.randint(50, 200)
        new_trf = db.add_trf(user_id, bonus)
        found = bonus
        
        await update.message.reply_text(
            f"🎉 ЗОЛОТАЯ ЖИЛА!\n"
            f"Найдено: {bonus} TRF\n"
            f"💰 Новый баланс: {new_trf} TRF\n"
            f"🤑 Удача на вашей стороне!"
        )
        outcome = "gold"
        
    else:
        # Обычная находка
        found = random.randint(5, 25)
        new_trf = db.add_trf(user_id, found)
        
        await update.message.reply_text(
            f"⛏️ Найдено торфа: {found} TRF\n"
            f"💰 Баланс: {new_trf} TRF\n"
            f"📈 Продолжайте разведку!"
        )
        outcome = "normal"
    
    # Запись в историю
    with db.get_connection() as conn:
        cur = conn.cursor()
        amount = found if outcome != 'co2' else -loss
        cur.execute('INSERT INTO mining (user_id, action, amount) VALUES (?, ?, ?)',
                   (user_id, f'torforazvedka_{outcome}', amount))
        conn.commit()

async def cmd_sobrat_kletchatku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /sobrat_kletchatku"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    now = datetime.now()
    last_cellulose = datetime.fromisoformat(user['last_cellulose'])
    
    if (now - last_cellulose).total_seconds() < CELLULOSE_COOLDOWN:
        wait_seconds = CELLULOSE_COOLDOWN - (now - last_cellulose).total_seconds()
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        await update.message.reply_text(f"🥬 Клетчатка ещё растёт! Ждите {hours}ч {minutes}мин.")
        return
    
    # Сбор клетчатки
    amount = KKL_PER_DAY + random.randint(-1, 2)  # 2-7 KKL
    new_kkl = db.add_kkl(user_id, amount)
    db.update_user(user_id, last_cellulose=now.isoformat())
    
    await update.message.reply_text(
        f"🥬 Собрано клетчатки: {amount} KKL\n"
        f"📦 Новый баланс: {new_kkl} KKL\n"
        f"⏳ Следующий сбор через 24 часа"
    )

async def cmd_kupit_kletchatku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /kupit_kletchatku"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    try:
        if not context.args or len(context.args) != 1:
            await update.message.reply_text("❌ Используйте: /kupit_kletchatku [количество]")
            return
        
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Количество должно быть положительным!")
            return
        
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден!")
            return
        
        # Курс: 1 KKL = 20 TRF
        cost = amount * 20
        
        if user['trf'] < cost:
            await update.message.reply_text(f"❌ Недостаточно TRF! Нужно {cost} TRF, у вас {user['trf']} TRF.")
            return
        
        # Покупка
        new_trf = user['trf'] - cost
        new_kkl = user['kkl'] + amount
        
        db.update_user(user_id, trf=new_trf, kkl=new_kkl)
        
        await update.message.reply_text(
            f"🛒 Покупка успешна!\n"
            f"📦 Куплено: {amount} KKL\n"
            f"💰 Потрачено: {cost} TRF\n"
            f"💎 Новый баланс: {new_trf} TRF | {new_kkl} KKL\n"
            f"📊 Курс: 1 KKL = 20 TRF"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Укажите число! Например: /kupit_kletchatku 5")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def passive_income_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача пассивного дохода"""
    db = context.bot_data.get('db')
    if not db:
        return
    
    while True:
        await asyncio.sleep(PASSIVE_INCOME_INTERVAL)
        # В python-telegram-bot можно использовать JobQueue для периодических задач
        # В данном случае оставляем как есть, но лучше переделать на JobQueue
        
        # Получаем всех пользователей
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id, last_passive_income FROM users')
            users = cur.fetchall()
        
        for user_id, last_income_str in users:
            last_income = datetime.fromisoformat(last_income_str)
            now = datetime.now()
            
            # Если прошло больше часа - начисляем доход
            if (now - last_income).total_seconds() >= 3600:
                hours_passed = int((now - last_income).total_seconds() // 3600)
                income = TRF_PER_HOUR * hours_passed
                
                if income > 0:
                    db.add_trf(user_id, income)
                    db.update_user(user_id, last_passive_income=now.isoformat())

def setup_economy_handlers(application: Application, db: Database):
    """Настройка обработчиков экономики"""
    # Сохраняем базу данных в bot_data
    application.bot_data['db'] = db
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler(["kopat_torf", "добыть_торф"], cmd_kopat_torf))
    application.add_handler(CommandHandler(["torforazvedka", "торфоразведка"], cmd_torforazvedka))
    application.add_handler(CommandHandler(["sobrat_kletchatku", "собрать_клетчатку"], cmd_sobrat_kletchatku))
    application.add_handler(CommandHandler(["kupit_kletchatku", "купить_клетчатку"], cmd_kupit_kletchatku))
    
    # Запускаем планировщик пассивного дохода
    # В python-telegram-bot лучше использовать JobQueue
    application.job_queue.run_once(
        lambda context: asyncio.create_task(passive_income_scheduler(context)),
        when=0
    )