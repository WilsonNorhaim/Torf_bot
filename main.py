import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes,
    ApplicationBuilder, JobQueue
)
from config import BOT_TOKEN
from database import Database
import handlers.commands as commands
import handlers.economy as economy
import handlers.court as court
import handlers.dangers as dangers
from datetime import datetime

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Middleware для проверки бана
async def check_ban_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка, забанен ли пользователь"""
    if not update.effective_user:
        return True
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user and user['is_banned'] and user['banned_until']:
        banned_until = datetime.fromisoformat(user['banned_until'])
        if banned_until > datetime.now():
            remaining = (banned_until - datetime.now()).total_seconds()
            from utils import format_time_remaining
            await update.message.reply_text(
                f"🚫 Вы изгнаны в болото! "
                f"Возвращение через: {format_time_remaining(remaining)}\n"
                f"Причина: нарушение Устава Торфяного Конгресса"
            )
            return False
        else:
            # Разбан если время вышло
            db.update_user(user_id, is_banned=False, banned_until=None)
    
    return True

# Обёртки для команд с проверкой бана
async def wrapped_command(handler, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обертка для команд с проверкой бана"""
    if not await check_ban_middleware(update, context):
        return
    
    # Добавляем db в context для использования в обработчиках
    context.user_data['db'] = db
    await handler(update, context, db)

# Фабрики команд
def create_command_handler(handler_func):
    """Создает обработчик команды с оберткой"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await wrapped_command(handler_func, update, context)
    return wrapper

# Фоновые задачи
async def danger_scheduler_wrapper(context: ContextTypes.DEFAULT_TYPE):
    """Обертка для планировщика опасностей"""
    await dangers.danger_scheduler(context.application, db)

async def passive_income_scheduler_wrapper(context: ContextTypes.DEFAULT_TYPE):
    """Обертка для пассивного дохода"""
    await economy.passive_income_scheduler(context.application, db)

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика для админа"""
    # Замените 123456789 на ваш ID
    if update.effective_user.id != 123456789:
        return
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT(*) FROM users')
        user_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM court_cases')
        case_count = cur.fetchone()[0]
        
        cur.execute('SELECT SUM(trf) FROM users')
        total_trf = cur.fetchone()[0] or 0
        
        cur.execute('SELECT SUM(kkl) FROM users')
        total_kkl = cur.fetchone()[0] or 0
    
    stats = f"""
📊 <b>АДМИН СТАТИСТИКА</b>

👥 Пользователей: {user_count}
⚖️ Судебных дел: {case_count}
💰 Всего TRF в системе: {total_trf}
🥬 Всего KKL в системе: {total_kkl}
"""
    
    await update.message.reply_text(stats, parse_mode="HTML")

def setup_handlers(application: Application):
    """Настройка всех обработчиков команд"""
    
    # Основные команды
    application.add_handler(CommandHandler("start", create_command_handler(commands.start_command)))
    application.add_handler(CommandHandler("status", create_command_handler(commands.status_command)))
    application.add_handler(CommandHandler("diagnostika", create_command_handler(commands.diagnostika_command)))
    application.add_handler(CommandHandler("диагностика", create_command_handler(commands.diagnostika_command)))
    application.add_handler(CommandHandler("aksioma", create_command_handler(commands.aksioma_command)))
    application.add_handler(CommandHandler("аксиома", create_command_handler(commands.aksioma_command)))
    application.add_handler(CommandHandler("novosti", create_command_handler(commands.novosti_command)))
    application.add_handler(CommandHandler("новости", create_command_handler(commands.novosti_command)))
    application.add_handler(CommandHandler("top", create_command_handler(commands.top_command)))
    application.add_handler(CommandHandler("help", create_command_handler(commands.help_command)))
    application.add_handler(CommandHandler("помощь", create_command_handler(commands.help_command)))
    application.add_handler(CommandHandler("moi_dela", create_command_handler(commands.moi_dela_command)))
    application.add_handler(CommandHandler("мои_дела", create_command_handler(commands.moi_dela_command)))
    
    # Команды лечения
    application.add_handler(CommandHandler("vnesti_izvest", create_command_handler(commands.vnesti_izvest_command)))
    application.add_handler(CommandHandler("внести_известь", create_command_handler(commands.vnesti_izvest_command)))
    application.add_handler(CommandHandler("podkormit_torfom", create_command_handler(commands.podkormit_torfom_command)))
    application.add_handler(CommandHandler("подкормить_торфом", create_command_handler(commands.podkormit_torfom_command)))
    application.add_handler(CommandHandler("podkislit", create_command_handler(commands.podkislit_command)))
    application.add_handler(CommandHandler("подкислить", create_command_handler(commands.podkislit_command)))
    application.add_handler(CommandHandler("ekstr_sredstvo", create_command_handler(commands.ekstr_sredstvo_command)))
    application.add_handler(CommandHandler("экстренное_средство", create_command_handler(commands.ekstr_sredstvo_command)))
    application.add_handler(CommandHandler("lechit_perforaciyu", create_command_handler(commands.lechit_perforaciyu_command)))
    application.add_handler(CommandHandler("лечить_перфорацию", create_command_handler(commands.lechit_perforaciyu_command)))
    
    # Экономика
    application.add_handler(CommandHandler("kopat_torf", create_command_handler(economy.kopat_torf_command)))
    application.add_handler(CommandHandler("добыть_торф", create_command_handler(economy.kopat_torf_command)))
    application.add_handler(CommandHandler("sobrat_kletchatku", create_command_handler(economy.sobrat_kletchatku_command)))
    application.add_handler(CommandHandler("собрать_клетчатку", create_command_handler(economy.sobrat_kletchatku_command)))
    application.add_handler(CommandHandler("torforazvedka", create_command_handler(economy.torforazvedka_command)))
    application.add_handler(CommandHandler("торфоразведка", create_command_handler(economy.torforazvedka_command)))
    application.add_handler(CommandHandler("kupit_kletchatku", create_command_handler(economy.kupit_kletchatku_command)))
    application.add_handler(CommandHandler("купить_клетчатку", create_command_handler(economy.kupit_kletchatku_command)))
    
    # Суды
    application.add_handler(CommandHandler("sud_selezenki", create_command_handler(court.sud_selezenki_command)))
    application.add_handler(CommandHandler("суд_селезёнки", create_command_handler(court.sud_selezenki_command)))
    application.add_handler(CommandHandler("sud_redodendrona", create_command_handler(court.sud_redodendrona_command)))
    application.add_handler(CommandHandler("суд_редодендрона", create_command_handler(court.sud_redodendrona_command)))
    application.add_handler(CommandHandler("sud_kishki", create_command_handler(court.sud_kishki_command)))
    application.add_handler(CommandHandler("суд_кишки", create_command_handler(court.sud_kishki_command)))
    
    # Защита
    application.add_handler(CommandHandler("zashita_co2", create_command_handler(dangers.zashita_co2_command)))
    application.add_handler(CommandHandler("защита_co2", create_command_handler(dangers.zashita_co2_command)))
    application.add_handler(CommandHandler("Kiparis_zashita", create_command_handler(dangers.kiparis_zashita_command)))
    application.add_handler(CommandHandler("кипарис_защита", create_command_handler(dangers.kiparis_zashita_command)))
    
    # Админ команды
    application.add_handler(CommandHandler("admin_stats", admin_stats_command))
    
    # Обработка обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, commands.echo))

async def on_startup(application: Application):
    """Действия при запуске бота"""
    logger.info("Торфобот запущен! Служу Торфяному Конгрессу! 🥬")
    
    # Уведомление админу
    try:
        await application.bot.send_message(
            chat_id=123456789,  # Замените на ваш ID
            text="✅ Торфобот запущен и готов служить Сети!"
        )
    except:
        pass

async def on_shutdown(application: Application):
    """Действия при остановке бота"""
    logger.info("Торфобот остановлен. Храните торф.")
    await application.bot.close()

def main():
    """Запуск бота"""
    # Создание приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Настройка обработчиков
    setup_handlers(application)
    
    # Настройка событий запуска/остановки
    application.add_handler(CommandHandler("start", create_command_handler(commands.start_command)))
    
    # Запуск фоновых задач
    job_queue = application.job_queue
    
    # Опасности каждые 3 часа
    job_queue.run_repeating(
        danger_scheduler_wrapper,
        interval=10800,  # 3 часа в секундах
        first=10  # Первый запуск через 10 секунд
    )
    
    # Пассивный доход каждый час
    job_queue.run_repeating(
        passive_income_scheduler_wrapper,
        interval=3600,  # 1 час
        first=30  # Первый запуск через 30 секунд
    )
    
    # Запуск бота
    application.run_polling(
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()