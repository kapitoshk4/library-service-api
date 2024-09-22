import stripe
from celery import shared_task
from django.utils import timezone
from borrowings.models import Borrowing
from borrowings.telegram_helper import send_telegram_message
from payments.models import Payment
from payments.utils import create_stripe_payment_session

FINE_MULTIPLAYER = 2


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


@shared_task
def check_expired_sessions():
    now = timezone.now()
    pending_payments = Payment.objects.filter(status="Pending")
    for payment in pending_payments:
        session = stripe.checkout.Session.retrieve(payment.session_id)
        if session["status"] == "expired" or session["expires_at"] < now.timestamp():
            payment.status = "Expired"
            payment.save()


@shared_task
def calculate_fines():
    today = timezone.now()
    borrowings = Borrowing.objects.filter(
        actual_return_date__isnull=True,
        expected_return_date=today
    )
    for borrowing in borrowings:
        days_overdue = (today - borrowing.expected_return_date).days
        if days_overdue > 0:
            fine_amount = days_overdue * borrowing.book.daily_fee * FINE_MULTIPLAYER
            create_stripe_payment_session(borrowing, current_request=None, payment_type="Fine", total_price=fine_amount)
