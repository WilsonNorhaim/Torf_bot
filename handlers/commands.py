import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils import generate_news, get_random_axiom, calculate_ph, format_time_remaining

# Вспомогательная функция для упоминаний
def format_user_mention_simple(user_id: int, username: str = None, first_name: str = None) -> str:
    """
    Создает кликабельное упоминание пользователя (упрощенная версия)
    """
    if username:
        return f'<a href="tg://user?id={user_id}">@{username}</a>'
    elif first_name:
        return f'<a href="tg://user?id={user_id}">{first_name}</a>'
    else:
        return f'<a href="tg://user?id={user_id}">Пользователь</a>'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    db.create_user(user_id, username, first_name)
    
    welcome_text = """🧪 Добро пожаловать в Торфяную Сеть

Я — Торфобот, Хранитель Сети, служитель Торфяного Конгресса.

Мои функции:
🪙 Экономика торфа (TRF) и клетчатки (KKL)
⚖️ Суды над нарушителями
⚠️ Оповещение об опасностях
🔬 Диагностика состояния чата

Основные команды:
/status — ваш баланс и здоровье
/diagnostika — диагностика чата
/aksioma — случайная аксиома
/novosti — новости Конгресса
/top — топ богачей

/sud_selezenki — суд за закисление
/sud_redodendrona — суд за пассивность
/sud_kishki — высшая мера

/kopat_torf — добыча торфа
/sobrat_kletchatku — сбор клетчатки

Да хранит вас Торфяной Конгресс"""
    
    await update.message.reply_text(welcome_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Ошибка: пользователь не найден! Напишите /start")
        return
    
    # Расчет риска перфорации
    risk = "низкий"
    if user['perforation_count'] >= 2:
        risk = "критический"
    elif user['perforation_count'] >= 1:
        risk = "высокий"
    elif user['warnings'] >= 2:
        risk = "средний"
    
    status_text = f"""🧪 Статус в Торфяной Сети

👤 Идентификация: {user['first_name']} (@{user['username'] or 'нет'})
🆔 ID: {user_id}

💰 Экономика:
🪙 Торф (TRF): {user['trf']}
🥬 Клетчатка (KKL): {user['kkl']}

⚕️ Здоровье:
🫀 Селезёночное здоровье: {user['health']}%
⚠️ Предупреждения: {user['warnings']}/3
🩸 Перфораций: {user['perforation_count']}
📊 Риск перфорации: {risk.upper()}

🔄 Состояние:
📅 В сети с: {user['created'][:10]}
🚫 Бан: {"ДА" if user['is_banned'] else "НЕТ"}"""
    
    await update.message.reply_text(status_text)

async def diagnostika_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    chat_id = update.effective_chat.id
    chat_data = db.get_chat(chat_id)
    
    ph = calculate_ph()
    
    # Обновляем pH в БД
    db.update_chat(chat_id, ph_level=ph)
    
    # Генерация диагноза
    if ph < 4.0:
        diagnosis = "🔥 КРИТИЧЕСКОЕ ЗАКИСЛЕНИЕ! Сеть на грани коллапса!"
        advice = "/vnesti_izvest - срочное известкование!"
        emoji = "☠️"
    elif ph < 5.5:
        diagnosis = "🌧️ Повышенная кислотность. Микориза угнетена."
        advice = "/podkormit_torfom - внести органику"
        emoji = "⚠️"
    elif 5.5 <= ph <= 6.5:
        diagnosis = "✅ Идеальный баланс! Сеть функционирует оптимально."
        advice = "Продолжайте в том же духе"
        emoji = "🌟"
    elif ph <= 7.5:
        diagnosis = "🌱 Легкая щелочность. Фотосинтез замедлен."
        advice = "/podkislit - внести торфяной субстрат"
        emoji = "🌿"
    else:
        diagnosis = "💀 ЩЕЛОЧНОЙ ШОК! Жизнедеятельность прекращена!"
        advice = "/ekstr_sredstvo - экстренные меры!"
        emoji = "🚨"
    
    report = f"""🔬 ДИАГНОСТИКА ЧАТА

{emoji} Диагноз: {diagnosis}
📊 pH уровень: {ph}
🌡️ Температура сети: {random.randint(15, 35)}°C
💨 CO₂ концентрация: {random.randint(350, 800)} ppm
🍄 Активность микоризы: {random.randint(30, 100)}%

💡 Рекомендация: {advice}

Последняя опасность: {chat_data.get('last_danger', 'не зафиксирована')}"""
    
    await update.message.reply_text(report)

async def aksioma_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    axiom = get_random_axiom()
    await update.message.reply_text(f"📜 Аксиома Торфяного Конгресса\n\n«{axiom}»")

async def novosti_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    news = generate_news()
    await update.message.reply_text(f"📰 НОВОСТИ ТОРФЯНОГО КОНГРЕССА\n\n{news}")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    top_users = db.get_top_users(10)
    
    if not top_users:
        await update.message.reply_text("📊 Топ пуст. Начните добывать торф!")
        return
    
    text = "🏆 <b>ТОП ХРАНИТЕЛЕЙ ТОРФЯНОЙ СЕТИ</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    titles = ["Верховный Хранитель", "Старший Хранитель", "Главный Хранитель", 
              "Хранитель Торфа", "Хранитель Клетчатки", "Страж pH", 
              "Защитник Микоризы", "Смотритель Сети", "Арбитр Селезёнки", "Новичок"]
    
    for i, (user_id, username, first_name, trf, kkl) in enumerate(top_users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        title = titles[i] if i < len(titles) else "Хранитель"
        
        # Используем титулы вместо имён
        display_name = title
        
        # Кликабельная ссылка на пользователя
        user_link = f'<a href="tg://user?id={user_id}">{display_name}</a>'
        
        text += f"{medal} {user_link}\n"
        text += f"   🪙 <code>{trf}</code> TRF | 🥬 <code>{kkl}</code> KKL\n\n"
    
    text += "\n👆 Имена кликабельны, но не упоминают пользователей"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    help_text = """🆘 ПОМОЩЬ ПО ТОРФОБОТУ

<b>Основные команды:</b>
/start — начало работы
/status — ваш статус
/top — топ пользователей
/help — эта справка

<b>Диагностика и лечение:</b>
/diagnostika — анализ состояния чата
/aksioma — случайная аксиома
/novosti — новости Конгресса
/vnesti_izvest — внести известь (2 KKL)
/podkormit_torfom — подкормить торфом (20 TRF)
/podkislit — подкислить чат (3 KKL)
/ekstr_sredstvo — экстренные меры (10 KKL)
/lechit_perforaciyu — лечить перфорацию (15 KKL)

<b>Экономика:</b>
/kopat_torf — добыча торфа
/sobrat_kletchatku — сбор клетчатки
/torforazvedka — рискованная добыча
/kupit_kletchatku [число] — купить клетчатку

<b>Суды (требуют KKL):</b>
/sud_selezenki @юзер — суд за токсичность (3 KKL)
/sud_redodendrona @юзер — суд за пассивность (5 KKL)
/sud_kishki @юзер — высшая мера (10 KKL)

<b>Защита:</b>
/zashita_co2 — защита от CO₂ (3 KKL)
/kiparis_zashita — защита от черепах

<b>Технические:</b>
/moi_dela — история ваших судов

💰 <b>Валюта:</b>
TRF (Торф) — основная валюта
KKL (Клетчатка) — премиум валюта

⚠️ <b>Опасности появляются автоматически раз в 3 часа</b>"""
    
    await update.message.reply_text(help_text, parse_mode="HTML")

async def moi_dela_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT court_type, verdict, result, timestamp 
        FROM court_cases 
        WHERE plaintiff_id = ? OR defendant_id = ?
        ORDER BY timestamp DESC LIMIT 10
        ''', (user_id, user_id))
        
        cases = cur.fetchall()
    
    if not cases:
        await update.message.reply_text("📂 У вас нет судебных дел.")
        return
    
    text = "⚖️ <b>ВАШИ СУДЕБНЫЕ ДЕЛА</b>\n\n"
    
    for i, (court_type, verdict, result, timestamp) in enumerate(cases, 1):
        role = "🟢 Истец" if court_type else "🔴 Ответчик"
        text += f"{i}. {role} | {court_type}\n"
        text += f"   📜 {verdict[:50]}...\n"
        text += f"   🏛️ Результат: {result}\n"
        text += f"   📅 {timestamp[:16]}\n\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def vnesti_izvest_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    try:
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден. Напишите /start")
            return
        
        if user['kkl'] < 2:
            await update.message.reply_text("❌ Недостаточно клетчатки для известкования! Нужно 2 KKL.")
            return
        
        # Снимаем KKL
        new_kkl = user['kkl'] - 2
        db.update_user(user_id, kkl=new_kkl)
        
        # Улучшаем pH чата
        chat_id = update.effective_chat.id
        chat_data = db.get_chat(chat_id)
        
        old_ph = chat_data.get('ph_level', 5.0)
        new_ph = min(7.0, old_ph + random.uniform(0.3, 0.8))
        db.update_chat(chat_id, ph_level=round(new_ph, 1))
        
        # Формируем ответ
        username = update.effective_user.username
        if username:
            user_text = f"@{username}"
        else:
            user_text = update.effective_user.first_name or "Пользователь"
        
        response = f"""✅ {user_text} внёс известь
pH чата улучшен: {old_ph:.1f} → {new_ph:.1f}
Списано: 2 KKL | Осталось: {new_kkl} KKL"""
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def podkormit_torfom_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['trf'] < 20:
        await update.message.reply_text("❌ Недостаточно торфа для подкормки! Нужно 20 TRF.")
        return
    
    # Снимаем торф
    new_trf = user['trf'] - 20
    db.update_user(user_id, trf=new_trf)
    
    # Улучшаем pH чата
    chat_id = update.effective_chat.id
    chat_data = db.get_chat(chat_id)
    old_ph = chat_data.get('ph_level', 5.0)
    new_ph = min(6.5, old_ph + random.uniform(0.1, 0.4))
    db.update_chat(chat_id, ph_level=round(new_ph, 1))
    
    # Формируем ответ
    username = update.effective_user.username
    if username:
        user_text = f"@{username}"
    else:
        user_text = update.effective_user.first_name or "Пользователь"
    
    response = f"""🌿 {user_text} подкормил чат торфом!
pH чата улучшен: {old_ph:.1f} → {new_ph:.1f}
Списано: 20 TRF | Осталось: {new_trf} TRF
🌱 Микориза благодарна!"""
    
    await update.message.reply_text(response)

async def podkislit_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['kkl'] < 3:
        await update.message.reply_text("❌ Недостаточно клетчатки для подкисления! Нужно 3 KKL.")
        return
    
    # Снимаем клетчатку
    new_kkl = user['kkl'] - 3
    db.update_user(user_id, kkl=new_kkl)
    
    # Слегка подкисляем чат (если слишком щелочной)
    chat_id = update.effective_chat.id
    chat_data = db.get_chat(chat_id)
    current_ph = chat_data.get('ph_level', 5.0)
    
    if current_ph > 6.5:
        new_ph = max(5.5, current_ph - random.uniform(0.2, 0.5))
        db.update_chat(chat_id, ph_level=round(new_ph, 1))
        
        username = update.effective_user.username
        if username:
            user_text = f"@{username}"
        else:
            user_text = update.effective_user.first_name or "Пользователь"
        
        response = f"""🌧️ {user_text} подкислил чат!
pH чата снижен: {current_ph:.1f} → {new_ph:.1f}
Списано: 3 KKL | Осталось: {new_kkl} KKL
💧 Баланс восстановлен!"""
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("ℹ️ Чату не требуется подкисление. pH в норме.")

async def ekstr_sredstvo_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['kkl'] < 10:
        await update.message.reply_text("❌ Недостаточно клетчатки для экстренных мер! Нужно 10 KKL.")
        return
    
    # Снимаем клетчатку
    new_kkl = user['kkl'] - 10
    db.update_user(user_id, kkl=new_kkl)
    
    # Экстренное восстановление pH
    chat_id = update.effective_chat.id
    chat_data = db.get_chat(chat_id)
    current_ph = chat_data.get('ph_level', 5.0)
    
    if current_ph < 4.0 or current_ph > 8.0:
        # Критическое значение - сбрасываем к норме
        new_ph = random.uniform(5.5, 6.5)
        db.update_chat(chat_id, ph_level=round(new_ph, 1))
        
        username = update.effective_user.username
        if username:
            user_text = f"@{username}"
        else:
            user_text = update.effective_user.first_name or "Пользователь"
        
        response = f"""🚨 {user_text} применил экстренные меры!
pH чата нормализован: {current_ph:.1f} → {new_ph:.1f}
Списано: 10 KKL | Осталось: {new_kkl} KKL
✅ Кризис миновал!"""
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("ℹ️ Экстренные меры не требуются. pH в допустимых пределах.")

async def lechit_perforaciyu_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if user['perforation_count'] == 0:
        await update.message.reply_text("ℹ️ У вас нет перфораций для лечения.")
        return
    
    if user['kkl'] < 15:
        await update.message.reply_text("❌ Недостаточно клетчатки для лечения! Нужно 15 KKL.")
        return
    
    # Лечение
    new_kkl = user['kkl'] - 15
    new_health = min(100, user['health'] + 30)
    db.update_user(user_id, 
                  kkl=new_kkl,
                  perforation_count=0,
                  health=new_health)
    
    await update.message.reply_text(
        f"💊 Лечение перфорации завершено!\n"
        f"🩸 Перфораций: {user['perforation_count']} → 0\n"
        f"🫀 Здоровье: {user['health']}% → {new_health}%\n"
        f"Списано: 15 KKL | Осталось: {new_kkl} KKL\n"
        f"✅ Вы здоровы!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    if update.message.text.startswith('/'):
        return
    await update.message.reply_text(f"Получено: {update.message.text}")