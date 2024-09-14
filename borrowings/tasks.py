from celery import shared_task
from django.utils import timezone
from borrowings.models import Borrowing
from borrowings.telegram_helper import send_telegram_message


@shared_task
def check_overdue_borrowings():
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=tomorrow,
        actual_return_date__isnull=True
    )
    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"📚 Overdue Borrowing Alert!\n"
                f"Book: {borrowing.book.title}\n"
                f"User: {borrowing.user.username}\n"
                f"Expected Return Date: {borrowing.expected_return_date}\n"
                f"Borrowing ID: {borrowing.id}\n"
            )
            send_telegram_message(message)
    else:
        send_telegram_message("🚫 No borrowings overdue today!")
