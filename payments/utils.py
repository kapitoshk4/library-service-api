import time

import stripe
from django.conf import settings
from django.urls import reverse

from payments.models import Payment

stripe.api_key = settings.STRIPE_API_KEY


def create_stripe_payment_session(borrowing, current_request, payment_type: str = "Payment", total_price: float = 0.0):
    success_url = current_request.build_absolute_uri(
        reverse("payments:payment-success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = current_request.build_absolute_uri(
        reverse("payments:payment-cancel")
    )
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
        success_url=success_url,
        cancel_url=cancel_url,
        expires_at=int(time.time() + 86400)
    )

    Payment.objects.create(
        status="Pending",
        borrowing=borrowing,
        session_id=session.id,
        session_url=session.url,
        type=payment_type,
        money_to_pay=total_price
    )
