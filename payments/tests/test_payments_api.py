from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from books.tests.test_books_api import sample_book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.utils import create_stripe_payment_session

PAYMENT_URL = reverse("payments:payment-list")


def detail_url(payment_id):
    return reverse("payments:payment-detail", args=(payment_id,))


def sample_user(**params):
    defaults = {
        "email": "test1@test.com",
        "password": "test1pass"
    }
    user_model = get_user_model()
    user = user_model.objects.filter(email=defaults["email"]).first()

    if not user:
        user = user_model.objects.create_user(**defaults)

    return user


def sample_borrowing(**params):
    defaults = {
        "borrow_date": timezone.now(),
        "expected_return_date": timezone.now() + timedelta(days=14),
        "actual_return_date": None,
        "book": sample_book(),
        "user": sample_user()
    }
    defaults.update(params)

    return Borrowing.objects.create(**defaults)


def sample_payment(borrowing, **params):
    defaults = {
        "status": Payment.Status.PENDING,
        "type": Payment.Type.PAYMENT,
        "session_url": "https://test-session.com",
        "session_id": "test_session_id",
        "money_to_pay": 10.00
    }
    defaults.update(params)
    return Payment.objects.create(borrowing=borrowing, **defaults)


class UnauthenticatedPaymentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPaymentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)
        self.borrowing = sample_borrowing(user=self.user)

    def test_list_payments(self):
        sample_payment(borrowing=self.borrowing)
        res = self.client.get(PAYMENT_URL)
        payments = Payment.objects.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), len(payments))

    def test_retrieve_payment_detail(self):
        payment = sample_payment(borrowing=self.borrowing)
        url = detail_url(payment.id)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], payment.id)

    def test_create_payment(self):
        borrowing = sample_borrowing(user=self.user)
        total_price = 20.00

        request = HttpRequest()
        request.build_absolute_uri = lambda x: f"http://testserver/{x}"

        create_stripe_payment_session(
            borrowing,
            current_request=request,
            total_price=total_price,
        )

        payments = Payment.objects.filter(borrowing=borrowing)
        self.assertEqual(payments.count(), 1)
        self.assertEqual(payments.first().money_to_pay, total_price)

    @patch("stripe.checkout.Session.retrieve")
    def test_payment_success(self, mock_stripe_retrieve):
        payment = sample_payment(borrowing=self.borrowing)
        payment.session_id = "test_session_id"
        payment.save()

        mock_stripe_retrieve.return_value = {
            "id": payment.session_id,
            "payment_status": "paid"
        }

        url = reverse("payments:payment-success")
        res = self.client.get(f"{url}?session_id={payment.session_id}")

        payment.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, Payment.Status.PAID)

    def test_payment_renew(self):
        payment = sample_payment(borrowing=self.borrowing)
        url = reverse("payments:payment-renew")

        res = self.client.post(url, {"session_id": payment.session_id})

        payments = Payment.objects.filter(borrowing=self.borrowing)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payments.count(), 1)
        self.assertNotEqual(payments.first().session_id, payment.session_id)


class AdminPaymentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="adminpass",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_payment_as_admin(self):
        borrowing = sample_borrowing(user=self.user)
        total_price = 20.00

        request = HttpRequest()
        request.build_absolute_uri = lambda x: f"http://testserver/{x}"

        create_stripe_payment_session(
            borrowing,
            current_request=request,
            total_price=total_price,
        )

        payments = Payment.objects.filter(borrowing=borrowing)
        self.assertEqual(payments.count(), 1)
        self.assertEqual(payments.first().money_to_pay, total_price)

    def test_list_payments_as_admin(self):
        sample_payment(borrowing=sample_borrowing(user=self.user))
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), Payment.objects.count())
