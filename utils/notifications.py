import sqlite3
import smtplib
import ssl
from email.message import EmailMessage

def get_upcoming_tasks(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, task_name, due_time, user_email
        FROM tasks
        WHERE due_time > DATETIME('now')
          AND due_time <= DATETIME('now', '+15 minutes')
    """)

    tasks = cur.fetchall()
    conn.close()
    return tasks

def send_email_reminder(to_email, task_name, due_time):
    msg = EmailMessage()
    msg["Subject"] = f"Reminder: '{task_name}' is due soon!"
    msg["From"] = "testingCS180@gmail.com"
    msg["To"] = to_email
    msg.set_content(f"Your task '{task_name}' is due at {due_time.strftime('%I:%M %p')}.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = ssl.create_default_context()) as server:
            server.login("testingCS180@gmail.com", "mukw qolm xwhj fcbw")
            server.send_message(msg)
        print(f"Reminder sent to {to_email} for task '{task_name}'.")
    except Exception as e:
        print(f"Error sending reminder to {to_email}: {e}")

def update_task_status(db_path, task_id, new_status):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""   """, (new_status, task_id))

    conn.commit()
    conn.close()