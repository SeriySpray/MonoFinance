import os
import sqlite3
import json
import threading
import time
import random
import tempfile
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
        except Exception as e:
            print(f"Error loading .env file: {e}")

load_env()

app = Flask(__name__)
app.secret_key = 'monofinance_secret_super_key_2026'
# Configure session cookie settings
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monofinance.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_kyiv_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Kyiv"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=3)))

def process_all_recurring_expenses():
    now = get_kyiv_now()
    today_str = now.strftime("%Y-%m-%d")
    today_day_num = now.day

    year = now.year
    month = now.month
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day_in_month = 31
    elif month in [4, 6, 9, 11]:
        max_day_in_month = 30
    else:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        max_day_in_month = 29 if is_leap else 28

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, transactions, recurring_expenses FROM user_data")
        rows = cursor.fetchall()
        
        updated_users_count = 0
        total_tx_added = 0

        for row in rows:
            user_id = row['user_id']
            try:
                transactions = json.loads(row['transactions']) if row['transactions'] else []
                recurring = json.loads(row['recurring_expenses']) if row['recurring_expenses'] else []
            except Exception:
                continue

            added_count = 0
            for item in recurring:
                scheduled_days = item.get('days')
                if not scheduled_days:
                    day_of_month = item.get('dayOfMonth', 1)
                    scheduled_days = [day_of_month]

                amount = item.get('amount', 0)
                description = item.get('description', '')
                if not amount or not description:
                    continue

                for scheduled_day in scheduled_days:
                    is_due_today = (today_day_num == scheduled_day) or (today_day_num == max_day_in_month and scheduled_day > max_day_in_month)
                    if is_due_today:
                        target_description = f"{description} (Автосписання)"
                        already_exists = any(
                            t.get('type') == 'expense' and 
                            t.get('description') == target_description and 
                            t.get('date') == today_str
                            for t in transactions
                        )
                        if not already_exists:
                            new_tx = {
                                "id": str(int(time.time() * 1000) + random.randint(1, 999)),
                                "amount": float(amount),
                                "type": "expense",
                                "description": target_description,
                                "date": today_str
                            }
                            transactions.append(new_tx)
                            added_count += 1

            if added_count > 0:
                cursor.execute(
                    "UPDATE user_data SET transactions = ? WHERE user_id = ?",
                    (json.dumps(transactions), user_id)
                )
                updated_users_count += 1
                total_tx_added += added_count

        if updated_users_count > 0:
            conn.commit()
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S Kyiv')}] Background recurring debit: added {total_tx_added} expense(s) for {updated_users_count} user(s).")
        conn.close()
    except Exception as e:
        print(f"Error in process_all_recurring_expenses: {e}")

def start_background_scheduler():
    def scheduler_loop():
        # Catch up immediately when server starts
        process_all_recurring_expenses()
        while True:
            time.sleep(600)  # Check every 10 minutes
            process_all_recurring_expenses()

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Create user_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER UNIQUE NOT NULL,
            transactions TEXT NOT NULL,
            savings_target REAL NOT NULL DEFAULT 10000.0,
            recurring_expenses TEXT NOT NULL,
            savings_goals TEXT DEFAULT '[]',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Check and perform migration if savings_goals or daily_expense_limit column is missing
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'savings_goals' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN savings_goals TEXT DEFAULT '[]'")
    if 'daily_expense_limit' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN daily_expense_limit REAL DEFAULT 1000.0")
    if 'weekly_expense_limit' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN weekly_expense_limit REAL DEFAULT 7000.0")
    if 'monthly_expense_limit' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN monthly_expense_limit REAL DEFAULT 30000.0")
    if 'expense_limit_period' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN expense_limit_period TEXT DEFAULT 'day'")
    
    conn.commit()

    # Pre-seed a default user 'serg' / 'password123' if not exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ('serg',))
    user = cursor.fetchone()
    if not user:
        p_hash = generate_password_hash('password123')
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('serg', p_hash))
        user_id = cursor.lastrowid
        
        # Initial sample seed data
        initial_transactions = [
            {
                "id": "1",
                "amount": 32000,
                "type": "income",
                "description": "Заробітна плата",
                "date": "2026-07-01"
            },
            {
                "id": "2",
                "amount": 1450,
                "type": "expense",
                "description": "Продукти супермаркет",
                "date": "2026-07-05"
            },
            {
                "id": "3",
                "amount": 4000,
                "type": "savings",
                "description": "Резервний фонд накопичення",
                "date": "2026-07-08"
            },
            {
                "id": "4",
                "amount": 450,
                "type": "expense",
                "description": "Кава та ланч в кафе",
                "date": "2026-07-10"
            },
            {
                "id": "5",
                "amount": 1800,
                "type": "expense",
                "description": "Комунальні послуги за дім",
                "date": "2026-07-12"
            },
            {
                "id": "6",
                "amount": 9500,
                "type": "income",
                "description": "Фріланс проєкт розробка",
                "date": "2026-07-15"
            },
            {
                "id": "7",
                "amount": 1500,
                "type": "savings",
                "description": "Накопичення на девайс",
                "date": "2026-07-18"
            }
        ]
        initial_recurring = []
        
        cursor.execute('''
            INSERT INTO user_data (user_id, transactions, savings_target, recurring_expenses)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(initial_transactions), 10000.0, json.dumps(initial_recurring)))
        conn.commit()

    conn.close()

# Initialize DB and start background scheduler on startup
init_db()
start_background_scheduler()

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory('.', 'app.js')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/favicon.svg')
def serve_favicon():
    return send_from_directory('.', 'favicon.svg')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('.', 'sw.js')

@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)):
        return send_from_directory('.', filename)
    return send_from_directory('.', 'index.html')


def get_request_data():
    data = request.get_json(silent=True, force=True)
    if not data or not isinstance(data, dict):
        try:
            raw_body = request.get_data(as_text=True)
            if raw_body:
                data = json.loads(raw_body)
        except Exception:
            pass
    if not data or not isinstance(data, dict):
        data = request.form.to_dict() or {}
    return data or {}

# Authentication API
@app.route('/api/register', methods=['POST'])
def register():
    data = get_request_data()
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))
    
    if not username or not password:
        return jsonify({'message': 'Ім\'я користувача та пароль є обов\'язковими'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Користувач з таким іменем вже існує'}), 400

    try:
        p_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, p_hash))
        user_id = cursor.lastrowid
        
        # Create empty initial data
        cursor.execute('''
            INSERT INTO user_data (user_id, transactions, savings_target, recurring_expenses, savings_goals, daily_expense_limit, weekly_expense_limit, monthly_expense_limit, expense_limit_period)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, json.dumps([]), 10000.0, json.dumps([]), json.dumps([]), 1000.0, 7000.0, 30000.0, 'day'))
        conn.commit()
        
        session.permanent = True
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'message': 'Реєстрація успішна', 'username': username}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Користувач з таким іменем вже існує'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = get_request_data()
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))
    
    if not username or not password:
        return jsonify({'message': 'Ім\'я користувача та пароль є обов\'язковими'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Вхід успішний', 'username': user['username']})
        
    return jsonify({'message': 'Неправильне ім\'я користувача або пароль'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'message': 'Вихід успішний'})

@app.route('/api/me', methods=['GET'])
def me():
    if 'user_id' in session:
        return jsonify({'username': session['username']})
    return jsonify({'message': 'Неавторизовано'}), 401

# Data Sync API
# Data Sync API
@app.route('/api/data', methods=['GET'])
def get_user_data():
    if 'user_id' not in session:
        return jsonify({'message': 'Неавторизовано'}), 401
        
    process_all_recurring_expenses()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT transactions, savings_target, recurring_expenses, savings_goals, daily_expense_limit, weekly_expense_limit, monthly_expense_limit, expense_limit_period FROM user_data WHERE user_id = ?", (session['user_id'],))
        row = cursor.fetchone()
    finally:
        conn.close()
    
    if not row:
        return jsonify({
            'transactions': [],
            'savingsTarget': 10000.0,
            'recurringExpenses': [],
            'savingsGoals': [],
            'dailyExpenseLimit': 1000.0,
            'weeklyExpenseLimit': 7000.0,
            'monthlyExpenseLimit': 30000.0,
            'expenseLimitPeriod': 'day'
        })
        
    txs = []
    if 'transactions' in row.keys() and row['transactions']:
        try:
            txs = json.loads(row['transactions'])
        except Exception:
            txs = []

    recurring = []
    if 'recurring_expenses' in row.keys() and row['recurring_expenses']:
        try:
            recurring = json.loads(row['recurring_expenses'])
        except Exception:
            recurring = []

    goals = []
    if 'savings_goals' in row.keys() and row['savings_goals']:
        try:
            goals = json.loads(row['savings_goals'])
        except Exception:
            goals = []

    daily_limit = 1000.0
    if 'daily_expense_limit' in row.keys() and row['daily_expense_limit'] is not None:
        try:
            daily_limit = float(row['daily_expense_limit'])
        except Exception:
            daily_limit = 1000.0

    weekly_limit = 7000.0
    if 'weekly_expense_limit' in row.keys() and row['weekly_expense_limit'] is not None:
        try:
            weekly_limit = float(row['weekly_expense_limit'])
        except Exception:
            weekly_limit = 7000.0

    monthly_limit = 30000.0
    if 'monthly_expense_limit' in row.keys() and row['monthly_expense_limit'] is not None:
        try:
            monthly_limit = float(row['monthly_expense_limit'])
        except Exception:
            monthly_limit = 30000.0

    limit_period = 'day'
    if 'expense_limit_period' in row.keys() and row['expense_limit_period']:
        limit_period = str(row['expense_limit_period'])

    s_target = 10000.0
    if 'savings_target' in row.keys() and row['savings_target'] is not None:
        try:
            s_target = float(row['savings_target'])
        except Exception:
            s_target = 10000.0

    return jsonify({
        'transactions': txs,
        'savingsTarget': s_target,
        'recurringExpenses': recurring,
        'savingsGoals': goals,
        'dailyExpenseLimit': daily_limit,
        'weeklyExpenseLimit': weekly_limit,
        'monthlyExpenseLimit': monthly_limit,
        'expenseLimitPeriod': limit_period
    })

@app.route('/api/data', methods=['POST'])
def save_user_data():
    if 'user_id' not in session:
        return jsonify({'message': 'Неавторизовано'}), 401
        
    data = get_request_data()
    transactions = data.get('transactions', [])
    savings_target = data.get('savingsTarget', 10000.0)
    recurring_expenses = data.get('recurringExpenses', [])
    savings_goals = data.get('savingsGoals', [])
    daily_expense_limit = data.get('dailyExpenseLimit', 1000.0)
    weekly_expense_limit = data.get('weeklyExpenseLimit', 7000.0)
    monthly_expense_limit = data.get('monthlyExpenseLimit', 30000.0)
    expense_limit_period = data.get('expenseLimitPeriod', 'day')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_data (user_id, transactions, savings_target, recurring_expenses, savings_goals, daily_expense_limit, weekly_expense_limit, monthly_expense_limit, expense_limit_period)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            transactions = excluded.transactions,
            savings_target = excluded.savings_target,
            recurring_expenses = excluded.recurring_expenses,
            savings_goals = excluded.savings_goals,
            daily_expense_limit = excluded.daily_expense_limit,
            weekly_expense_limit = excluded.weekly_expense_limit,
            monthly_expense_limit = excluded.monthly_expense_limit,
            expense_limit_period = excluded.expense_limit_period
    ''', (session['user_id'], json.dumps(transactions), float(savings_target), json.dumps(recurring_expenses), json.dumps(savings_goals), float(daily_expense_limit), float(weekly_expense_limit), float(monthly_expense_limit), str(expense_limit_period)))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Дані успішно збережено'}), 200
    
@app.route('/api/voice-transcribe', methods=['POST'])
def voice_transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'Аудіофайл не знайдено'}), 400
        
    audio_file = request.files['audio']
    temp_dir = tempfile.gettempdir()
    orig_name = audio_file.filename or 'voice.webm'
    ext = os.path.splitext(orig_name)[1]
    if not ext:
        ext = '.webm'
    file_path = os.path.join(temp_dir, f"voice_{int(time.time())}{ext}")
    audio_file.save(file_path)
    
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    
    transcribed_text = ""
    
    try:
        # 1. Try Groq Whisper API if key is present
        if groq_api_key:
            import requests
            mime_type = audio_file.content_type or 'audio/webm'
            with open(file_path, 'rb') as f:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_api_key}"},
                    files={"file": (os.path.basename(file_path), f, mime_type)},
                    data={"model": "whisper-large-v3-turbo", "language": "uk"}
                )
            if response.status_code == 200:
                transcribed_text = response.json().get("text", "")
                
        # 2. Try OpenAI Whisper API if key is present
        elif openai_api_key:
            import requests
            with open(file_path, 'rb') as f:
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {openai_api_key}"},
                    files={"file": (os.path.basename(file_path), f, "audio/webm")},
                    data={"model": "whisper-1", "language": "uk"}
                )
            if response.status_code == 200:
                transcribed_text = response.json().get("text", "")
    except Exception as e:
        print(f"Error in transcription API: {e}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    if not transcribed_text:
        return jsonify({
            'success': False if (groq_api_key or openai_api_key) else True,
            'text': transcribed_text,
            'message': 'API ключ не налаштовано на сервері або помилка розпізнавання'
        })
        
    return jsonify({
        'success': True,
        'text': transcribed_text
    })

ALLOWED_EXPENSE_CATEGORIES = [
    "Продукти харчування",
    "Кафе та ресторани",
    "Транспорт та Авто",
    "Комунальні та Житло",
    "Здоров'я та Спорт",
    "Покупки та Одяг",
    "Розваги та Дозвілля",
    "Інші витрати"
]

ALLOWED_INCOME_CATEGORIES = [
    "Зарплата",
    "Фріланс та Проєкти",
    "Премії та Чайові",
    "Інвестиції та Кешбек",
    "Інші доходи"
]

def fallback_categorize(desc, tx_type):
    d = desc.lower().strip() if desc else ''
    if not d:
        return 'Інші доходи' if tx_type == 'income' else 'Інші витрати'
    if 'конверт' in d:
        return 'Конверти'

    if tx_type == 'income':
        if any(w in d for w in ['зарплат', 'salary', 'робот', 'аванс', 'стипенд']):
            return 'Зарплата'
        if any(w in d for w in ['фріланс', 'freelance', 'проєкт', 'проект']):
            return 'Фріланс та Проєкти'
        if any(w in d for w in ['чайов', 'tip', 'бонус', 'премі']):
            return 'Премії та Чайові'
        if any(w in d for w in ['дивіденд', 'dividend', 'акці', 'інвест', 'кешбек', 'cashback', 'повернен']):
            return 'Інвестиції та Кешбек'
        return 'Інші доходи'
    else:
        # Check Cafe & Restaurant first
        if any(w in d for w in ['кава', 'coffee', 'cafe', 'кафе', 'ланч', 'обід', 'сніданок', 'вечер', 'перекус', 'ресторан', 'макдональдз', 'mcdonald', 'кфс', 'kfc', 'піца', 'pizza', 'суші', 'sushi', 'burger', 'бургер', 'бар', 'пиво', 'заклад', 'шаурм', 'шаверм', 'хот-дог', 'хотдог', 'сендвіч', 'глово', 'glovo', 'bolt food', 'паста', 'суп', 'салат', 'борщ', 'вареник', 'пельмен']):
            return 'Кафе та ресторани'
        # Check Groceries & Food (including bakery: кексики, кекс, булочка, філе, фарш, стейк, etc.)
        if any(w in d for w in ['булочк', 'булк', 'хліб', 'батон', 'пиріж', 'пирог', 'круасан', 'кекс', 'кексик', 'філе', 'фарш', 'стейк', 'печив', 'вафл', 'торт', 'тістечк', 'пряник', 'сир', 'молок', 'масл', 'сметан', 'йогурт', 'кефір', 'м\'яс', 'мяс', 'ковбас', 'сосиск', 'курк', 'курчат', 'риб', 'овоч', 'фрукт', 'яблук', 'банан', 'картопл', 'помідор', 'огірок', 'ківі', 'кавун', 'авокадо', 'полуниц', 'ягод', 'морозив', 'креветк', 'супермаркет', 'продукт', 'їж', 'food', 'купув', 'сільпо', 'атб', 'ашан', 'metro', 'маркет', 'магазин', 'пачка', 'шоколад', 'цукерк', 'солодощ', 'снек', 'чипс', 'горіх', 'пакет', 'вода', 'сік', 'напій', 'чай', 'какао']):
            return 'Продукти харчування'
        if any(w in d for w in ['проїзд', 'таксі', 'taxi', 'метро', 'автобус', 'тролейбус', 'квиток', 'транспорт', 'убер', 'uber', 'uklon', 'уклон', 'bolt', 'бензин', 'газ', 'окко', 'wog', 'пальне', 'заправк', 'автомийк', 'сто', 'авто']):
            return 'Транспорт та Авто'
        if any(w in d for w in ['комунал', 'оренд', 'rent', 'світл', 'газ', 'вод', 'квартплат', 'інтернет', 'домофон', 'дім', 'кварт']):
            return 'Комунальні та Житло'
        if any(w in d for w in ['спорт', 'gym', 'fitness', 'зал', 'тренуван', 'аптек', 'ліки', 'лікар', 'медиц', 'здоров']):
            return 'Здоров\'я та Спорт'
        if any(w in d for w in ['одяг', 'взутт', 'шопінг', 'покупк', 'технік', 'телефон', 'придбав', 'купив']):
            return 'Покупки та Одяг'
        if any(w in d for w in ['кіно', 'театр', 'ігр', 'гра', 'подпіск', 'підписк', 'netflix', 'spotify', 'розваг']):
            return 'Розваги та Дозвілля'
        return 'Інші витрати'

CATEGORY_ICON_MAP = {
    "Продукти харчування": "shopping_cart",
    "Кафе та ресторани": "restaurant",
    "Транспорт та Авто": "directions_car",
    "Комунальні та Житло": "home",
    "Здоров'я та Спорт": "fitness_center",
    "Покупки та Одяг": "shopping_bag",
    "Розваги та Дозвілля": "movie",
    "Інші витрати": "receipt_long",
    "Зарплата": "work",
    "Фріланс та Проєкти": "computer",
    "Премії та Чайові": "redeem",
    "Інвестиції та Кешбек": "trending_up",
    "Інші доходи": "payments",
    "Конверти": "account_balance_wallet"
}

@app.route('/api/categorize', methods=['POST'])
def categorize_transaction():
    data = request.get_json(silent=True, force=True) or {}
    description = data.get('description', '').strip()
    tx_type = data.get('type', 'expense')
    
    if not description:
        def_cat = 'Інші витрати' if tx_type == 'expense' else 'Інші доходи'
        return jsonify({'success': True, 'category': def_cat, 'icon': CATEGORY_ICON_MAP.get(def_cat, 'receipt_long')})
        
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    
    cat_result = None
    
    allowed_cats = ALLOWED_EXPENSE_CATEGORIES if tx_type == 'expense' else ALLOWED_INCOME_CATEGORIES

    if groq_api_key:
        try:
            import requests
            prompt = f"""Ти інтелектуальний фінансовий аналітик додатка MonoFinance.
Твоє завдання — проаналізувати зміст і контекст опису транзакції та обрати найвідповіднішу категорію зі списку.
Давай моделі повну свободу семантичного розпізнавання природної мови, побутових назв продуктів, страв, покупок та послуг.

СЕМАНТИЧНИЙ ОПИС КАТЕГОРИЗАЦІЇ ВИТРАТ:
- 'Продукти харчування': Будь-які продукти з магазину, сировина, випічка (кексики, кекси, булочки, круасани, хліб, батон), м'ясо (філе, фарш, стейки, птиця, свинина), риба, овочі, фрукти, ягоди, молочка, сир, десерти, солодощі, інгредієнти, супермаркети, пачка товарів, безалкогольні напої тощо.
- 'Кафе та ресторани': Готова їжа з закладів, кав'ярні, фастфуд, обіди, сніданки, вечері, ресторани, бари, доставки (Glovo, Bolt Food), піца, суші, бургери, шаурма.
- 'Транспорт та Авто': Таксі, метро, проїзд, квитки, паливо, заправки, автомийки, ремонт авто.
- 'Комунальні та Житло': Комуналка, оренда житла, інтернет, світло, вода, газ, ремонт.
- 'Здоров'я та Спорт': Аптеки, ліки, медичні послуги, лікарі, аналізи, спортзал, тренування.
- 'Покупки та Одяг': Одяг, взуття, шопінг, техніка, електроніка, гаджети, покупки для дому.
- 'Розваги та Дозвілля': Кіно, ігри, підписки (Netflix, Spotify), концерти, хобі.
- 'Інші витрати': Використовуй ТІЛЬКИ якщо опис не має жодного відношення до харчування, покупок або транспортних послуг.

Список дозволених категорій: {allowed_cats}

Поверни ЛИШЕ валідний JSON у форматі {{"category": "Назва з списку"}}.

Опис операції: "{description}"
Тип операції: {tx_type}"""

            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=0.8
            )
            if resp.status_code == 200:
                res_data = resp.json()
                content = res_data['choices'][0]['message']['content']
                parsed = json.loads(content)
                candidate = parsed.get("category", "").strip()
                if candidate in allowed_cats:
                    cat_result = candidate
        except Exception as e:
            print(f"Groq categorization error: {e}")
            
    elif openai_api_key:
        try:
            import requests
            prompt = f"""Ти інтелектуальний фінансовий аналітик додатка MonoFinance.
Проаналізуй опис транзакції та ОБЕРИ ТОЧНО ОДНУ із дозволених категорій.

Список дозволених категорій: {allowed_cats}
Поверни ЛИШЕ JSON об'єкт у форматі {{"category": "Назва з списку"}}.

Опис операції: "{description}"
Тип операції: {tx_type}"""

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=0.8
            )
            if resp.status_code == 200:
                res_data = resp.json()
                content = res_data['choices'][0]['message']['content']
                parsed = json.loads(content)
                candidate = parsed.get("category", "").strip()
                if candidate in allowed_cats:
                    cat_result = candidate
        except Exception as e:
            print(f"OpenAI categorization error: {e}")

    if not cat_result:
        cat_result = fallback_categorize(description, tx_type)

    icon_name = CATEGORY_ICON_MAP.get(cat_result, 'receipt_long')

    return jsonify({
        'success': True,
        'category': cat_result,
        'icon': icon_name
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
