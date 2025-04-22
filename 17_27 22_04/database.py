import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    created_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    word TEXT,
                    correct INTEGER,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    conn.commit()
    conn.close()


def add_user(user_id, username):
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
              (user_id, username, datetime.now()))
    conn.commit()
    conn.close()


def save_quiz_result(user_id, word, correct):
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("SELECT correct FROM quiz_results WHERE user_id = ? AND word = ? ORDER BY timestamp DESC LIMIT 1",
              (user_id, word))
    result = c.fetchone()
    if result:
        c.execute("UPDATE quiz_results SET correct = ?, timestamp = ? WHERE user_id = ? AND word = ?",
                  (correct, datetime.now(), user_id, word))
    else:
        c.execute("INSERT INTO quiz_results (user_id, word, correct, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, word, correct, datetime.now()))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT word) FROM quiz_results WHERE user_id = ?", (user_id,))
    total_words = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ? AND correct = 1", (user_id,))
    correct_answers = c.fetchone()[0] or 0
    conn.close()
    return total_words, correct_answers


def view_all_data():
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    print("=== Users ===")
    for user in users:
        print(f"User ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
    c.execute("SELECT * FROM quiz_results")
    results = c.fetchall()
    print("\n=== Quiz Results ===")
    for result in results:
        print(f"ID: {result[0]}, User ID: {result[1]}, Word: {result[2]}, Correct: {result[3]}, Timestamp: {result[4]}")
    conn.close()