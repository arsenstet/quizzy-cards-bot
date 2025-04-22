import sqlite3
from datetime import datetime


def init_db():
    """Ініціалізація бази даних SQLite."""
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_results
                 (user_id INTEGER, word TEXT, correct INTEGER, timestamp TEXT,
                  PRIMARY KEY (user_id, word))''')  # Унікальний ключ на user_id і word
    conn.commit()
    conn.close()


def add_user(user_id, username):
    """Додавання нового користувача."""
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
              (user_id, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def save_quiz_result(user_id, word, correct):
    """Збереження або оновлення результату квіза."""
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    # Переконуємося, що correct — це 0 або 1
    correct = 1 if correct else 0
    # Спробуємо оновити, якщо запис існує
    c.execute("""
        UPDATE quiz_results
        SET correct = ?, timestamp = ?
        WHERE user_id = ? AND word = ?
    """, (correct, datetime.now().isoformat(), user_id, word))
    # Якщо оновлення не відбулося, додаємо новий запис
    if c.rowcount == 0:
        c.execute("""
            INSERT INTO quiz_results (user_id, word, correct, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, word, correct, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Отримання статистики користувача."""
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(word), SUM(correct)
        FROM quiz_results
        WHERE user_id = ?
    """, (user_id,))
    total_words, correct_answers = c.fetchone()
    conn.close()
    return total_words or 0, correct_answers or 0


def view_all_data():
    """Перегляд усіх записів у базі даних."""
    conn = sqlite3.connect('quizzy_cards.db')
    c = conn.cursor()

    print("=== Users ===")
    c.execute("SELECT user_id, username, created_at FROM users")
    users = c.fetchall()
    for user in users:
        print(f"User ID: {user[0]}, Username: {user[1]}, Created At: {user[2]}")

    print("\n=== Quiz Results ===")
    c.execute("SELECT user_id, word, correct, timestamp FROM quiz_results")
    results = c.fetchall()
    for result in results:
        print(f"User ID: {result[0]}, Word: {result[1]}, Correct: {result[2]}, Timestamp: {result[3]}")

    conn.close()