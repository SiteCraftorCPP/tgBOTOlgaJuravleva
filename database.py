import aiosqlite
from config import DB_NAME

async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, существует ли пользователь, если нет — добавляем
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, username, full_name, balance)
            VALUES (?, ?, ?, 0)
        ''', (user_id, username, full_name))
        
        # Обновляем имя и username на случай их изменения
        await db.execute('''
            UPDATE users SET username = ?, full_name = ? WHERE user_id = ?
        ''', (username, full_name, user_id))
        
        await db.commit()

async def update_balance(user_id: int, amount: int):
    """Изменяет баланс пользователя на amount (может быть отрицательным)"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        await db.commit()
        
        # Возвращаем новый баланс
        async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_top_users(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, full_name, balance, username FROM users ORDER BY balance DESC LIMIT ?', (limit,)) as cursor:
            return await cursor.fetchall()

async def reset_all_balances():
    """Обнуляет баланс SCN коинов у всех участников."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET balance = 0')
        await db.commit()
