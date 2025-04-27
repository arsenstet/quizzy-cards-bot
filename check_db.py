import psycopg2
import os

def view_all_data():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT user_id, word, correct, timestamp FROM quiz_results")
    results = c.fetchall()
    conn.close()
    return users, results

if __name__ == "__main__":
    users, results = view_all_data()
    print("=== Users ===")
    for user in users:
        print(f"User ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
    print("\n=== Quiz Results ===")
    for result in results:
        print(f"User ID: {result[0]}, Word: {result[1]}, Correct: {result[2]}, Timestamp: {result[3]}")