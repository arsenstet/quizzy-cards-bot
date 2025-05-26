import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Налаштування підключення до бази даних
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Перевірка змінних середовища
if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
    logging.error("One or more database environment variables are missing")
    raise ValueError("One or more database environment variables are missing")

# Ініціалізація бази даних
def init_db():
    try:
        logging.info("Attempting to connect to the database...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()

        # Створення таблиці users
        logging.info("Creating table 'users' if it does not exist...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Створення таблиці quiz_results
        logging.info("Creating table 'quiz_results' if it does not exist...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                word TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Створення таблиці scores для балів
        logging.info("Creating table 'scores' if it does not exist...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                score INTEGER DEFAULT 0,
                username TEXT NOT NULL
            )
        ''')

        # Перевірка, чи таблиці створені
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in c.fetchall()]
        logging.info(f"Tables in database: {tables}")

        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise

# Додавання користувача
def add_user(user_id, username):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING', (user_id, username))
        # Перевіряємо, чи існує запис у scores, і додаємо, якщо його немає
        c.execute('INSERT INTO scores (user_id, score, username) VALUES (%s, 0, %s) ON CONFLICT (user_id) DO NOTHING', (user_id, username))
        conn.commit()
        conn.close()
        logging.info(f"User {user_id} added successfully")
    except Exception as e:
        logging.error(f"Error adding user {user_id}: {e}")
        raise

# Збереження результату квіза
def save_quiz_result(user_id, word, is_correct):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('INSERT INTO quiz_results (user_id, word, is_correct) VALUES (%s, %s, %s)', (user_id, word, is_correct))
        if is_correct:
            c.execute('UPDATE scores SET score = score + 1 WHERE user_id = %s', (user_id,))
            # Логування для перевірки оновлення
            c.execute('SELECT score FROM scores WHERE user_id = %s', (user_id,))
            new_score = c.fetchone()[0]
            logging.info(f"Updated score for user {user_id} to {new_score}")
        conn.commit()
        conn.close()
        logging.info(f"Quiz result for user {user_id} saved successfully")
    except Exception as e:
        logging.error(f"Error saving quiz result for user {user_id}: {e}")
        raise

# Отримання статистики користувача
def get_user_stats(user_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM quiz_results WHERE user_id = %s', (user_id,))
        total_words = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM quiz_results WHERE user_id = %s AND is_correct = TRUE', (user_id,))
        correct_answers = c.fetchone()[0]
        c.execute('SELECT score FROM scores WHERE user_id = %s', (user_id,))
        score = c.fetchone()
        score = score[0] if score else 0
        conn.close()
        return total_words, correct_answers, score
    except Exception as e:
        logging.error(f"Error getting stats for user {user_id}: {e}")
        raise

# Отримання лідерборду
def get_leaderboard():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('SELECT user_id, username, score FROM scores ORDER BY score DESC LIMIT 5')
        top_players = c.fetchall()
        c.execute('SELECT COUNT(*) FROM scores')
        total_users = c.fetchone()[0]
        conn.close()
        return top_players, total_users
    except Exception as e:
        logging.error(f"Error getting leaderboard: {e}")
        raise

# Отримання місця користувача в лідерборді
def get_user_rank(user_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('SELECT COUNT(*) + 1 FROM scores WHERE score > (SELECT score FROM scores WHERE user_id = %s)', (user_id,))
        rank = c.fetchone()[0]
        conn.close()
        return rank
    except Exception as e:
        logging.error(f"Error getting rank for user {user_id}: {e}")
        raise

# Перегляд усіх даних (для адміністратора)
def view_all_data():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode="require"
        )
        c = conn.cursor()
        c.execute('SELECT * FROM users')
        users = c.fetchall()
        c.execute('SELECT * FROM quiz_results')
        results = c.fetchall()
        conn.close()
        return users, results
    except Exception as e:
        logging.error(f"Error viewing all data: {e}")
        raise