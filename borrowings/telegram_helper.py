import os
import requests
from dotenv import load_dotenv

from borrowings.models import Borrowing

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")


def send_borrowing_notification(borrowing: Borrowing):
    message = (
        f"📚 New Borrowing Created:\n"
        f"User: {borrowing.user.full_name}\n"
        f"Book: {borrowing.book.title}\n"
        f"Borrow Date: {borrowing.borrow_date}\n"
        f"Expected Return Date: {borrowing.expected_return_date}"
        f"Actual Return Date: {borrowing.actual_return_date}"
    )
    send_telegram_message(message)


