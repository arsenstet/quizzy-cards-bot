import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
    logging.error("One or more database environment variables are missing")
    raise ValueError("One or more database environment variables are missing")

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

        logging.info("Creating table 'users' if it does not exist...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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
        conn.close()
        return total_words, correct_answers
    except Exception as e:
        logging.error(f"Error getting stats for user {user_id}: {e}")
        raise

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