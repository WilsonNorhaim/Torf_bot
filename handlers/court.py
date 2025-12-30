import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils import get_court_verdict, format_time_remaining
from config import COURT_COSTS

async def sud_selezenki_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    # Проверка формата - нужен ответ на сообщение
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Используйте команду ответом на сообщение пользователя!")
        return
    
    plaintiff_id = update.effective_user.id
    plaintiff = db.get_user(plaintiff_id)
    
    if not plaintiff or plaintiff['kkl'] < COURT_COSTS["selezenka"]:
        await update.message.reply_text(f"❌ Недостаточно клетчатки! Нужно {COURT_COSTS['selezenka']} KKL.")
        return
    
    # Определяем ответчика из ответа на сообщение
    defendant_id = update.message.reply_to_message.from_user.id
    defendant = db.get_user(defendant_id)
    
    if not defendant:
        await update.message.reply_text("❌ Ответчик не зарегистрирован в системе!")
        return
    
    # Нельзя судить себя
    if plaintiff_id == defendant_id:
        await update.message.reply_text("❌ Нельзя подать в суд на самого себя!")
        return
    
    # Проверяем бан ответчика
    if defendant and defendant.get('is_banned'):
        await update.message.reply_text("❌ Этот пользователь уже изгнан в болото!")
        return
    
    # Снимаем KKL с истца
    new_kkl = plaintiff['kkl'] - COURT_COSTS["selezenka"]
    db.update_user(plaintiff_id, kkl=new_kkl)
    
    await update.message.reply_text("⚖️ Идёт заседание Суда Двенадцатиперстной Селезёнки...")
    
    # Имитация заседания
    await asyncio.sleep(2)
    
    # Вердикт
    verdict_text, fine = get_court_verdict("selezenka")
    
    # Случайный результат
    result = random.choice(["guilty", "not_guilty", "warning"])
    
    if "виновен" in verdict_text.lower() or result == "guilty":
        # Обвинительный приговор
        if defendant['trf'] >= fine:
            # Штраф
            new_def_trf = defendant['trf'] - fine
            db.update_user(defendant_id, trf=new_def_trf)
            result_msg = f"Штраф {fine} TRF"
            
            # Добавляем TRF в общий фонд (или истцу)
            new_pla_trf = plaintiff['trf'] + fine
            db.update_user(plaintiff_id, trf=new_pla_trf)
        else:
            # Предупреждение
            warnings = defendant.get('warnings', 0) + 1
            db.update_user(defendant_id, warnings=warnings)
            result_msg = f"Предупреждение {warnings}/3"
            
            if warnings >= 3:
                # Перфорация!
                perforation_count = defendant.get('perforation_count', 0) + 1
                db.update_user(defendant_id, 
                              perforation_count=perforation_count,
                              warnings=0,
                              health=max(0, defendant.get('health', 100) - 30))
                result_msg = "АНАЛЬНАЯ ПЕРФОРАЦИЯ! Отправлен в суглинки на лечение!"
    else:
        result_msg = "Оправдан"
    
    # Запись дела
    db.add_court_case(plaintiff_id, defendant_id, "selezenka", verdict_text, fine, result_msg)
    
    # Формируем ответ
    plaintiff_name = f"@{plaintiff['username']}" if plaintiff.get('username') else plaintiff.get('first_name', 'Пользователь')
    defendant_name = f"@{defendant['username']}" if defendant.get('username') else defendant.get('first_name', 'Пользователь')
    
    response = f"""⚖️ <b>ВЕРДИКТ СУДА СЕЛЕЗЁНКИ</b>

👤 <b>Истец:</b> {plaintiff_name}
👤 <b>Ответчик:</b> {defendant_name}

📜 <b>Приговор:</b> {verdict_text}

🏛️ <b>Результат:</b> {result_msg}

💰 <b>С истца списано:</b> {COURT_COSTS['selezenka']} KKL
💎 <b>Баланс истца:</b> {new_kkl} KKL"""
    
    await update.message.reply_text(response, parse_mode="HTML")

async def sud_redodendrona_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Используйте команду ответом на сообщение!")
        return
    
    plaintiff_id = update.effective_user.id
    defendant_id = update.message.reply_to_message.from_user.id
    
    plaintiff = db.get_user(plaintiff_id)
    defendant = db.get_user(defendant_id)
    
    if not plaintiff or plaintiff['kkl'] < COURT_COSTS["redodendron"]:
        await update.message.reply_text(f"❌ Недостаточно клетчатки! Нужно {COURT_COSTS['redodendron']} KKL.")
        return
    
    if not defendant:
        await update.message.reply_text("❌ Ответчик не найден!")
        return
    
    # Нельзя судить себя
    if plaintiff_id == defendant_id:
        await update.message.reply_text("❌ Нельзя подать в суд на самого себя!")
        return
    
    # Снимаем KKL
    new_kkl = plaintiff['kkl'] - COURT_COSTS["redodendron"]
    db.update_user(plaintiff_id, kkl=new_kkl)
    
    await update.message.reply_text("🌿 Суд Редодендрона рассматривает дело о нарушении фотосинтеза...")
    await asyncio.sleep(3)
    
    # Вердикт
    verdict_text, fine = get_court_verdict("redodendron")
    
    # Шанс 70% на обвинение
    if random.random() < 0.7:
        # Обвинение
        if defendant['trf'] >= fine:
            new_def_trf = defendant['trf'] - fine
            db.update_user(defendant_id, trf=new_def_trf)
            
            # Клетчатка в фонд чата (упрощенная реализация - просто начисляем истцу)
            new_pla_kkl = plaintiff['kkl'] + 2  # +2 KKL за победу
            db.update_user(plaintiff_id, kkl=new_pla_kkl)
            
            result_msg = f"Штраф {fine} TRF, истец получает 2 KKL"
        else:
            # Альтернативное наказание
            health_loss = random.randint(10, 30)
            new_health = max(0, defendant.get('health', 100) - health_loss)
            db.update_user(defendant_id, health=new_health)
            result_msg = f"Потеря здоровья: -{health_loss}%"
    else:
        result_msg = "Оправдан. Иск отклонён"
    
    db.add_court_case(plaintiff_id, defendant_id, "redodendron", verdict_text, fine, result_msg)
    
    plaintiff_name = f"@{plaintiff['username']}" if plaintiff.get('username') else plaintiff.get('first_name', 'Пользователь')
    defendant_name = f"@{defendant['username']}" if defendant.get('username') else defendant.get('first_name', 'Пользователь')
    
    response = f"""🌿 <b>ВЕРДИКТ СУДА РЕДОДЕНДРОНА</b>

👤 <b>Истец:</b> {plaintiff_name}
👤 <b>Ответчик:</b> {defendant_name}

📜 <b>Приговор:</b> {verdict_text}

🏛️ <b>Результат:</b> {result_msg}

💰 <b>С истца списано:</b> {COURT_COSTS['redodendron']} KKL"""
    
    await update.message.reply_text(response, parse_mode="HTML")

async def sud_kishki_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Используйте команду ответом на сообщение!")
        return
    
    plaintiff_id = update.effective_user.id
    defendant_id = update.message.reply_to_message.from_user.id
    
    if plaintiff_id == defendant_id:
        await update.message.reply_text("❌ Нельзя изгнать самого себя!")
        return
    
    plaintiff = db.get_user(plaintiff_id)
    defendant = db.get_user(defendant_id)
    
    if not plaintiff or plaintiff['kkl'] < COURT_COSTS["kishka"]:
        await update.message.reply_text(f"❌ Недостаточно клетчатки! Нужно {COURT_COSTS['kishka']} KKL.")
        return
    
    if not defendant:
        await update.message.reply_text("❌ Ответчик не найден!")
        return
    
    # Проверка на бан ответчика
    if defendant.get('is_banned'):
        await update.message.reply_text("❌ Этот пользователь уже изгнан в болото!")
        return
    
    # Снимаем KKL
    new_kkl = plaintiff['kkl'] - COURT_COSTS["kishka"]
    db.update_user(plaintiff_id, kkl=new_kkl)
    
    await update.message.reply_text("🩸 Суд Прямой Кишки начинает высшее слушание...")
    await asyncio.sleep(4)
    
    # Вердикт
    verdict_text, fine = get_court_verdict("kishka")
    
    # 50% шанс на изгнание
    if random.random() < 0.5 and "изгнан" in verdict_text.lower():
        # Изгнание на 24 часа
        ban_until = (datetime.now() + timedelta(hours=24)).isoformat()
        db.update_user(defendant_id, 
                      is_banned=True,
                      banned_until=ban_until,
                      warnings=0,
                      health=50)
        
        result_msg = "ИЗГНАН В БОЛОТО НА 24 ЧАСА!"
        
        # Штраф в пользу истца
        if defendant.get('trf', 0) > 0:
            penalty = min(defendant['trf'], 100)
            new_def_trf = defendant['trf'] - penalty
            new_pla_trf = plaintiff['trf'] + penalty
            db.update_user(defendant_id, trf=new_def_trf)
            db.update_user(plaintiff_id, trf=new_pla_trf)
            result_msg += f"\nКонфисковано {penalty} TRF в пользу истца"
    else:
        result_msg = "Дело отклонено. Недостаточно доказательств."
    
    db.add_court_case(plaintiff_id, defendant_id, "kishka", verdict_text, fine, result_msg)
    
    plaintiff_name = f"@{plaintiff['username']}" if plaintiff.get('username') else plaintiff.get('first_name', 'Пользователь')
    defendant_name = f"@{defendant['username']}" if defendant.get('username') else defendant.get('first_name', 'Пользователь')
    
    response = f"""🩸 <b>ВЕРДИКТ СУДА ПРЯМОЙ КИШКИ</b>

👤 <b>Истец:</b> {plaintiff_name}
👤 <b>Ответчик:</b> {defendant_name}

📜 <b>Приговор:</b> {verdict_text}

🏛️ <b>Результат:</b> {result_msg}

💰 <b>С истца списано:</b> {COURT_COSTS['kishka']} KKL
⚠️ <b>Высшая мера применена!</b>"""
    
    await update.message.reply_text(response, parse_mode="HTML")