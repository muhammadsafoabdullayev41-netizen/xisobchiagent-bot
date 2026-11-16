import sqlite3
from datetime import datetime
from config import DB_FILE

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        current_cycle_id INTEGER,
        is_active INTEGER DEFAULT 1
    )
    """)
    
    # Oylik hisob-kitob davrlari (Cycles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP,
        initial_income REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    """)
    
    # Tranzaksiyalar (Kirim va Chiqim)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cycle_id INTEGER,
        type TEXT, -- 'kirim' yoki 'chiqim'
        amount REAL,
        category TEXT,
        description TEXT,
        raw_text TEXT,
        receipt_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(cycle_id) REFERENCES cycles(id)
    )
    """)
    
    # Foydalanuvchi xabarlari / faoliyat jurnali (Admin uchun)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        action_type TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("""
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        conn.commit()
        
        # Yangi foydalanuvchi uchun boshlang'ich davr ochamiz
        cycle_id = start_new_cycle(user_id, "1-oy hisobi")
        cursor.execute("UPDATE users SET current_cycle_id = ? WHERE user_id = ?", (cycle_id, user_id))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        # Ism va username o'zgargan bo'lsa yangilaymiz
        cursor.execute("""
        UPDATE users SET username = ?, first_name = ?, last_name = ?
        WHERE user_id = ?
        """, (username, first_name, last_name, user_id))
        conn.commit()
        
        # Agar joriy davr yo'q bo'lsa ochamiz
        if not user['current_cycle_id']:
            cycle_id = start_new_cycle(user_id, "Joriy oy")
            cursor.execute("UPDATE users SET current_cycle_id = ? WHERE user_id = ?", (cycle_id, user_id))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
    conn.close()
    return user

def log_activity(user_id: int, username: str, first_name: str, action_type: str, content: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO activity_logs (user_id, username, first_name, action_type, content)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, action_type, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log xatoligi: {e}")

def start_new_cycle(user_id: int, title: str = None, initial_income: float = 0.0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Oldingi faol davrlarni yopamiz
    cursor.execute("""
    UPDATE cycles SET status = 'closed', end_date = CURRENT_TIMESTAMP
    WHERE user_id = ? AND status = 'active'
    """, (user_id,))
    
    if not title:
        now_str = datetime.now().strftime("%B %Y")
        title = f"{now_str} hisoboti"
        
    cursor.execute("""
    INSERT INTO cycles (user_id, title, initial_income, status)
    VALUES (?, ?, ?, 'active')
    """, (user_id, title, initial_income))
    cycle_id = cursor.lastrowid
    
    cursor.execute("UPDATE users SET current_cycle_id = ? WHERE user_id = ?", (cycle_id, user_id))
    
    # Agar boshlang'ich oylik/pul kiritilgan bo'lsa, uni kirim tranzaksiyasi sifatida qo'shamiz
    if initial_income > 0:
        cursor.execute("""
        INSERT INTO transactions (user_id, cycle_id, type, amount, category, description, raw_text)
        VALUES (?, ?, 'kirim', ?, 'Oylik', 'Boshlang''ich oylik/daromad', 'Boshlang''ich balans')
        """, (user_id, cycle_id, initial_income))
        
    conn.commit()
    conn.close()
    return cycle_id

def add_transaction(user_id: int, trans_type: str, amount: float, category: str, description: str, raw_text: str = "", receipt_path: str = None) -> int:
    user = get_or_create_user(user_id)
    cycle_id = user['current_cycle_id']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO transactions (user_id, cycle_id, type, amount, category, description, raw_text, receipt_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, cycle_id, trans_type, amount, category, description, raw_text, receipt_path))
    trans_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trans_id

def delete_transaction(trans_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (trans_id, user_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def get_current_stats(user_id: int):
    user = get_or_create_user(user_id)
    cycle_id = user['current_cycle_id']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cycle ma'lumotlari
    cursor.execute("SELECT * FROM cycles WHERE id = ?", (cycle_id,))
    cycle = cursor.fetchone()
    
    # Jami kirim
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) as total FROM transactions
    WHERE cycle_id = ? AND type = 'kirim'
    """, (cycle_id,))
    total_income = cursor.fetchone()['total']
    
    # Jami chiqim
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) as total FROM transactions
    WHERE cycle_id = ? AND type = 'chiqim'
    """, (cycle_id,))
    total_expense = cursor.fetchone()['total']
    
    # Kategoriyalar bo'yicha chiqimlar
    cursor.execute("""
    SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
    FROM transactions
    WHERE cycle_id = ? AND type = 'chiqim'
    GROUP BY category
    ORDER BY total DESC
    """, (cycle_id,))
    expense_categories = cursor.fetchall()
    
    # Kategoriyalar bo'yicha kirimlar
    cursor.execute("""
    SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
    FROM transactions
    WHERE cycle_id = ? AND type = 'kirim'
    GROUP BY category
    ORDER BY total DESC
    """, (cycle_id,))
    income_categories = cursor.fetchall()
    
    # Oxirgi 10 ta tranzaksiya
    cursor.execute("""
    SELECT * FROM transactions
    WHERE cycle_id = ?
    ORDER BY id DESC
    LIMIT 10
    """, (cycle_id,))
    recent_transactions = cursor.fetchall()
    
    conn.close()
    
    balance = total_income - total_expense
    
    return {
        "cycle_title": cycle['title'] if cycle else "Joriy oy",
        "cycle_start": cycle['start_date'] if cycle else "",
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "expense_categories": expense_categories,
        "income_categories": income_categories,
        "recent_transactions": recent_transactions
    }

def get_all_users_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    cnt = cursor.fetchone()['cnt']
    conn.close()
    return cnt

def get_users_list(limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.*, 
           (SELECT COUNT(*) FROM transactions t WHERE t.user_id = u.user_id) as trans_count,
           (SELECT MAX(created_at) FROM activity_logs l WHERE l.user_id = u.user_id) as last_seen
    FROM users u
    ORDER BY u.created_at DESC
    LIMIT ?
    """, (limit,))
    users = cursor.fetchall()
    conn.close()
    return users

def get_recent_activity_logs(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM activity_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_user_logs(target_user_id: int, limit: int = 25):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM activity_logs
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (target_user_id, limit))
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_admin_system_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as users_count FROM users")
    users_count = cursor.fetchone()['users_count']
    
    cursor.execute("SELECT COUNT(*) as total_trans, COALESCE(SUM(amount), 0) as sum_trans FROM transactions")
    trans_stat = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as total_logs FROM activity_logs")
    total_logs = cursor.fetchone()['total_logs']
    
    conn.close()
    return {
        "users_count": users_count,
        "total_transactions": trans_stat['total_trans'],
        "total_volume": trans_stat['sum_trans'],
        "total_logs": total_logs
    }
