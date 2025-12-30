from telegram.ext import Application, CommandHandler, ContextTypes
import random
import asyncio
from datetime import datetime
from database import Database
from config import DANGER_INTERVAL
from telegram import Update

# Глобальный словарь для активных черепашек
active_turtles = {}

async def danger_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача опасностей"""
    db = context.bot_data.get('db')
    if not db:
        return
    
    while True:
        await asyncio.sleep(DANGER_INTERVAL)
        
        # Получаем все чаты
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT chat_id FROM chats')
            chats = cur.fetchall()
        
        for (chat_id,) in chats:
            # Случайная опасность
            danger_type = random.choice(["co2", "turtles", "perforation"])
            
            if danger_type == "co2":
                await send_co2_danger(context.bot, chat_id, db)
            elif danger_type == "turtles":
                await send_turtle_danger(context.bot, chat_id, db)
            elif danger_type == "perforation":
                await send_perforation_danger(context.bot, chat_id, db)
            
            # Обновляем время последней опасности
            db.update_chat(chat_id, last_danger=datetime.now().isoformat())

async def send_co2_danger(bot, chat_id, db):
    """Опасность CO2"""
    db.update_chat(chat_id, co2_active=True)
    
    text = """
⚠️ *ВНИМАНИЕ: ПОВЫШЕНИЕ CO₂!*

В атмосфере чата обнаружена критическая концентрация углекислого газа!

📊 *Уровень:* {} ppm
🌡️ *Температура:* +{}°C

*Последствия:*
• Все участники теряют 15 TRF
• Селезёночное здоровье -20%
• Риск перфорации повышен

🛡️ *Защита:* 
Используйте /zashita_co2 (3 KKL) для нейтрализации!
    """.format(random.randint(800, 1500), random.randint(2, 8))
    
    try:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    except:
        pass  # Игнорируем ошибки отправки

async def send_turtle_danger(bot, chat_id, db):
    """Опасность черепашек"""
    db.update_chat(chat_id, turtle_active=True)
    
    # Генерируем случайное количество черепашек
    turtle_count = random.randint(3, 8)
    turtles = "🐢" * turtle_count
    
    text = f"""
🐢 *ЧЕРЕПАШКИ ТАТУНХАМОНА АТАКУЮТ!*

{turtles}

*Опасность:* Пожирают торфяные запасы!
• -10 TRF каждые 5 минут
• Активность микоризы -30%

🛡️ *Защита:*
СРОЧНО: /Kiparis_zashita
Нужно минимум 5 участников для отражения!

⏰ *Время на реакцию:* 10 минут
    """
    
    # Сохраняем черепашек
    active_turtles[chat_id] = {
        'count': turtle_count,
        'start_time': datetime.now(),
        'participants': set()
    }
    
    try:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    except:
        pass
    
    # Таймер для ущерба
    asyncio.create_task(turtle_damage_timer(bot, chat_id, db))

async def send_perforation_danger(bot, chat_id, db):
    """Случайная перфорация"""
    # Получаем всех пользователей чата
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM users WHERE is_banned = FALSE')
        users = cur.fetchall()
    
    if not users:
        return
    
    # Выбираем случайную жертву
    victim_id = random.choice(users)[0]
    victim = db.get_user(victim_id)
    
    if not victim:
        return
    
    # Наносим урон
    health_loss = random.randint(20, 50)
    new_health = max(0, victim['health'] - health_loss)
    perforation_count = victim['perforation_count'] + 1
    
    db.update_user(victim_id, 
                  health=new_health,
                  perforation_count=perforation_count)
    
    victim_name = f"@{victim['username']}" if victim['username'] else victim['first_name']
    
    text = f"""
🩸 *АНАЛЬНАЯ ПЕРФОРАЦИЯ!*

*Пострадавший:* {victim_name}
⚕️ *Потеря здоровья:* -{health_loss}%
🩸 *Перфораций всего:* {perforation_count}

*Симптомы:*
• Невозможность добычи торфа (24 часа)
• Селезёночная недостаточность
• Требуется лечение в суглинках

💊 *Лечение:* 
Автоматическое через 24 часа
Или /lechit_perforaciyu (15 KKL)
    """
    
    try:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    except:
        pass

async def turtle_damage_timer(bot, chat_id, db):
    """Таймер ущерба от черепашек"""
    await asyncio.sleep(300)  # 5 минут
    
    if chat_id not in active_turtles:
        return
    
    # Наносим ущерб всем пользователям
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, trf FROM users')
        users = cur.fetchall()
    
    damage_report = "🐢 *Черепашки наносят урон!*\n\n"
    
    for user_id, trf in users:
        damage = min(10, trf)  # Не больше 10 TRF
        if damage > 0:
            new_trf = max(0, trf - damage)
            db.update_user(user_id, trf=new_trf)
            
            user = db.get_user(user_id)
            name = f"@{user['username']}" if user['username'] else user['first_name']
            damage_report += f"{name}: -{damage} TRF\n"
    
    damage_report += f"\n🛡️ Защищайтесь: /Kiparis_zashita"
    
    try:
        await bot.send_message(chat_id, damage_report, parse_mode="Markdown")
    except:
        pass

async def cmd_kiparis_zashita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /Kiparis_zashita"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    chat_id = update.effective_chat.id
    
    if chat_id not in active_turtles:
        await update.message.reply_text("🐢 Черепашек нет. Можно расслабиться.")
        return
    
    user_id = update.effective_user.id
    turtles = active_turtles[chat_id]
    
    # Добавляем участника защиты
    turtles['participants'].add(user_id)
    
    participant_count = len(turtles['participants'])
    needed = 5
    
    if participant_count >= needed:
        # Успешная защита
        del active_turtles[chat_id]
        db.update_chat(chat_id, turtle_active=False)
        
        # Награда участникам
        reward = random.randint(5, 15)
        for pid in turtles['participants']:
            db.add_trf(pid, reward)
        
        await update.message.reply_text(
            f"🛡️ *КИПАРИСОВАЯ ЗАЩИТА АКТИВИРОВАНА!*\n\n"
            f"🐢 Черепашки Татунхамона отброшены!\n"
            f"👥 Участников защиты: {participant_count}\n"
            f"💰 Награда каждому: {reward} TRF\n"
            f"🎉 Опасность миновала!",
            parse_mode="Markdown"
        )
    else:
        # Нужно больше участников
        await update.message.reply_text(
            f"🛡️ *Защита формируется...*\n\n"
            f"👥 Участников: {participant_count}/{needed}\n"
            f"🐢 Черепашек осталось: {turtles['count']}\n"
            f"⏰ Призывайте других: /Kiparis_zashita",
            parse_mode="Markdown"
        )

async def cmd_zashita_co2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /zashita_co2"""
    db = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных")
        return
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['kkl'] < 3:
        await update.message.reply_text("❌ Недостаточно клетчатки! Нужно 3 KKL.")
        return
    
    chat_id = update.effective_chat.id
    chat_data = db.get_chat(chat_id)
    
    if not chat_data.get('co2_active'):
        await update.message.reply_text("⚠️ Угрозы CO₂ нет в данный момент.")
        return
    
    # Снимаем KKL
    new_kkl = user['kkl'] - 3
    db.update_user(user_id, kkl=new_kkl)
    
    # Деактивируем опасность
    db.update_chat(chat_id, co2_active=False)
    
    # Награда за защиту
    reward = random.randint(20, 50)
    new_trf = db.add_trf(user_id, reward)
    
    username = update.effective_user.username
    name_mention = f"@{username}" if username else update.effective_user.first_name
    
    await update.message.reply_text(
        f"🛡️ *ЗАЩИТА ОТ CO₂ АКТИВИРОВАНА!*\n\n"
        f"👤 Защитник: {name_mention}\n"
        f"🥬 Потрачено: 3 KKL\n"
        f"💰 Награда: {reward} TRF\n"
        f"💎 Новый баланс: {new_trf} TRF | {new_kkl} KKL\n"
        f"🌿 Опасность нейтрализована!",
        parse_mode="Markdown"
    )

def setup_handlers(application: Application, db: Database):
    """Настройка обработчиков"""
    # Сохраняем базу данных в bot_data для доступа из контекста
    application.bot_data['db'] = db
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler(["Kiparis_zashita", "кипарис_защита"], cmd_kiparis_zashita))
    application.add_handler(CommandHandler(["zashita_co2", "защита_co2"], cmd_zashita_co2))
    
    # Запускаем планировщик опасностей
    application.job_queue.run_once(
        lambda context: asyncio.create_task(danger_scheduler(context)),
        when=0
    )