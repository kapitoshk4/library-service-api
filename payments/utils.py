import stripe
from django.conf import settings

from payments.models import Payment

stripe.api_key = settings.STRIPE_API_KEY


def create_stripe_payment_session(borrowing):
    borrow_duration = (
            borrowing.expected_return_date - borrowing.borrow_date
    ).days
    daily_fee = borrowing.book.daily_fee
    total_price = borrow_duration * daily_fee
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": borrowing.book.title,
                },
                "unit_amount": int(total_price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    Payment.objects.create(
        status="Pending",
        borrowing=borrowing,
        session_id=session.id,
        session_url=session.url,
        type="Payment",
        money_to_pay=total_price
    )
