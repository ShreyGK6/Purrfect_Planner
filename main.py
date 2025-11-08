import smtplib
import ssl
from email.message import EmailMessage

msg = EmailMessage()
msg.set_content("This is a test email sent from a Python script.")
msg["Subject"] = "GMAIL Test"
msg["From"] = "testingCS180@gmail.com"
msg["To"] = "shrey.kothari@email.ucr.edu"

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = ssl.create_default_context()) as server:
        server.login("testingCS180@gmail.com", "mukw qolm xwhj fcbw")
        server.send_message(msg)
    print("Email sent successfully!")

except Exception as e:
    print(f"An error occurred: {e}")