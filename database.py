import sqlite3
import json
from datetime import datetime, timedelta
import os

class Database:
    def __init__(self, db_path='data/torfobot.db'):
        os.makedirs('data', exist_ok=True)
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # Пользователи
            cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                trf INTEGER DEFAULT 100,
                kkl INTEGER DEFAULT 5,
                health INTEGER DEFAULT 100,
                warnings INTEGER DEFAULT 0,
                last_passive_income TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_cellulose TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE,
                banned_until TIMESTAMP,
                perforation_count INTEGER DEFAULT 0,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Чаты
            cur.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                ph_level REAL DEFAULT 5.0,
                last_danger TIMESTAMP,
                danger_type TEXT,
                turtle_active BOOLEAN DEFAULT FALSE,
                co2_active BOOLEAN DEFAULT FALSE
            )
            ''')
            
            # Суды
            cur.execute('''
            CREATE TABLE IF NOT EXISTS court_cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plaintiff_id INTEGER,
                defendant_id INTEGER,
                court_type TEXT,
                verdict TEXT,
                fine INTEGER,
                result TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plaintiff_id) REFERENCES users (user_id),
                FOREIGN KEY (defendant_id) REFERENCES users (user_id)
            )
            ''')
            
            # Добыча
            cur.execute('''
            CREATE TABLE IF NOT EXISTS mining (
                user_id INTEGER,
                action TEXT,
                amount INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            conn.commit()
    
    def create_user(self, user_id, username, first_name):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name) 
            VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
    
    def get_user(self, user_id):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            columns = [column[0] for column in cur.description]
            user = cur.fetchone()
            return dict(zip(columns, user)) if user else None
    
    def update_user(self, user_id, **kwargs):
        if not kwargs:
            return
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            cur.execute(f'UPDATE users SET {set_clause} WHERE user_id = ?', values)
            conn.commit()
    
    def add_trf(self, user_id, amount):
        user = self.get_user(user_id)
        if user:
            new_trf = user['trf'] + amount
            self.update_user(user_id, trf=new_trf)
            return new_trf
        return 0
    
    def add_kkl(self, user_id, amount):
        user = self.get_user(user_id)
        if user:
            new_kkl = user['kkl'] + amount
            self.update_user(user_id, kkl=new_kkl)
            return new_kkl
        return 0
    
    def get_chat(self, chat_id):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
            columns = [column[0] for column in cur.description]
            chat = cur.fetchone()
            if chat:
                return dict(zip(columns, chat))
            else:
                # Создаем запись чата если нет
                cur.execute('INSERT INTO chats (chat_id) VALUES (?)', (chat_id,))
                conn.commit()
                return {
                    'chat_id': chat_id, 
                    'ph_level': 5.0, 
                    'last_danger': None, 
                    'danger_type': None, 
                    'turtle_active': False, 
                    'co2_active': False
                }
    
    def update_chat(self, chat_id, **kwargs):
        with self.get_connection() as conn:
            cur = conn.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [chat_id]
            cur.execute(f'UPDATE chats SET {set_clause} WHERE chat_id = ?', values)
            conn.commit()
    
    def add_court_case(self, plaintiff_id, defendant_id, court_type, verdict, fine, result):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            INSERT INTO court_cases (plaintiff_id, defendant_id, court_type, verdict, fine, result)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (plaintiff_id, defendant_id, court_type, verdict, fine, result))
            conn.commit()
            return cur.lastrowid
    
    def get_active_bans(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            SELECT user_id, banned_until FROM users 
            WHERE is_banned = TRUE AND banned_until > datetime('now')
            ''')
            return {row[0]: row[1] for row in cur.fetchall()}
    
    def get_top_users(self, limit=10):
        """Получение топ пользователей с first_name"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            SELECT user_id, username, first_name, trf, kkl FROM users 
            ORDER BY trf DESC LIMIT ?
            ''', (limit,))
            return cur.fetchall()
    
    def get_user_full(self, user_id):
        """Получение полной информации о пользователе"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            columns = [column[0] for column in cur.description]
            user = cur.fetchone()
            return dict(zip(columns, user)) if user else None
    
    def get_all_users(self):
        """Получение всех пользователей"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users WHERE is_banned = FALSE')
            return [row[0] for row in cur.fetchall()]
    
    def reset_daily_limits(self):
        """Сброс дневных лимитов (для планировщика)"""
        # Эта функция может использоваться для сброса дневных ограничений
        pass
    
    def log_mining(self, user_id, action, amount):
        """Логирование добычи"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            INSERT INTO mining (user_id, action, amount) 
            VALUES (?, ?, ?)
            ''', (user_id, action, amount))
            conn.commit()
    
    def get_user_mining_history(self, user_id, limit=10):
        """История добычи пользователя"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
            SELECT action, amount, timestamp 
            FROM mining 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            return cur.fetchall()