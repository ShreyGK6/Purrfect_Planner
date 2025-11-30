import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler

notifications_bp = Blueprint('notifications', __name__) 
scheduler = BackgroundScheduler()
scheduler.start()

EMAIL_ADDRESS = "testingCS180@gmail.com"
EMAIL_PASSWORD = "mukw qolm xwhj fcbw"  

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

def update_task_status(db_path, task_id, new_status):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET status = ?
        WHERE id = ?
    """, (new_status, task_id))
    conn.commit()
    conn.close()

def send_email_reminder(to_email, task_name, due_time):
    msg = EmailMessage()
    msg["Subject"] = f"Reminder: '{task_name}' is due soon!"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(f"Your task '{task_name}' is due at {due_time.strftime('%I:%M %p')}.")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Reminder sent to {to_email} for task '{task_name}'.")
        return True, f"Reminder sent to {to_email} for task '{task_name}'."
    except Exception as e:
        print(f"Error sending reminder to {to_email}: {e}")
        return False, str(e)

@notifications_bp.route("/notifications", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        to_email = request.form.get("email")
        task_name = request.form.get("task_name")
        due_time_str = request.form.get("due_time")

        try:
            due_time_str = due_time_str.replace("T", " ")
            due_time = datetime.strptime(due_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid due time format!", "error")
            return redirect(url_for("notifications.index"))

        reminder_time = due_time - timedelta(minutes = 10)

        if reminder_time < datetime.now():
            reminder_time = datetime.now() + timedelta(seconds = 5)

        scheduler.add_job(send_email_reminder,
            'date',
            run_date = reminder_time,
            args = [to_email, task_name, due_time])

        flash(f"Reminder scheduled for {reminder_time.strftime('%Y-%m-%d %I:%M %p')}", "success")
        return redirect(url_for("notifications.index"))

    return render_template("index.html")