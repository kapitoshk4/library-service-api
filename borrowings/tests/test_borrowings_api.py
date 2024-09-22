from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from rest_framework.test import APIClient

from books.tests.test_books_api import sample_book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingRetrieveSerializer, BorrowingSerializer

BORROWING_URL = reverse("borrowings:borrowing-list")


def detail_url(borrow_id):
    return reverse("borrowings:borrowing-detail", args=(borrow_id,))


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


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_borrowings(self):
        sample_book()

        res = self.client.get(BORROWING_URL)
        books = Borrowing.objects.all()
        serializer = BorrowingListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_borrowings_by_is_active(self):
        borrowing1 = sample_borrowing(actual_return_date=None, user=self.user)
        actual_return_date = timezone.now() + timedelta(days=7)
        borrowing2 = sample_borrowing(actual_return_date=actual_return_date, user=self.user)

        borrowing1.refresh_from_db()
        borrowing2.refresh_from_db()

        res = self.client.get(
            BORROWING_URL, {"is_active": "true"}
        )

        serializer_borrowing1 = BorrowingListSerializer(borrowing1)
        serializer_borrowing2 = BorrowingListSerializer(borrowing2)

        self.assertIn(serializer_borrowing1.data, res.data["results"])
        self.assertNotIn(serializer_borrowing2.data, res.data["results"])

    def test_retrieve_borrowing_detail(self):
        borrowing = sample_borrowing(user=self.user)
        borrowing.refresh_from_db()
        url = detail_url(borrowing.id)

        res = self.client.get(url)
        serializer = BorrowingRetrieveSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_borrowing_by_users(self):
        user2 = sample_user(email="user2@test.com", password="password2")
        borrowing1 = sample_borrowing(user=self.user)
        borrowing2 = sample_borrowing(user=user2)
        borrowing1.refresh_from_db()
        borrowing2.refresh_from_db()

        res = self.client.get(
            BORROWING_URL, {"users": user2.id}
        )
        serializer_borrowing1 = BorrowingListSerializer(borrowing1)
        serializer_borrowing2 = BorrowingListSerializer(borrowing2)

        self.assertIn(serializer_borrowing1.data, res.data["results"])
        self.assertNotIn(serializer_borrowing2.data, res.data["results"])

    def test_borrowing_return(self):
        borrowing1 = sample_borrowing(user=self.user)
        actual_return_date = timezone.now() + timedelta(days=7)
        borrowing2 = sample_borrowing(user=self.user, actual_return_date=actual_return_date)
        borrowing1.refresh_from_db()
        borrowing2.refresh_from_db()

        url1 = detail_url(borrowing1.id) + "return/"
        url2 = detail_url(borrowing2.id) + "return/"

        res1 = self.client.post(url1)
        res2 = self.client.post(url2)

        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)


class AdminBorrowingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_borrowing(self):
        payload = {
            "borrow_date": timezone.now(),
            "expected_return_date": timezone.now() + timedelta(days=14),
            "book": sample_book().id,
            "user": self.user.id
        }

        res = self.client.post(BORROWING_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_filter_borrowing_by_users(self):
        user2 = sample_user(email="user2@test.com", password="password2")
        borrowing1 = sample_borrowing(user=self.user)
        borrowing2 = sample_borrowing(user=user2)
        borrowing1.refresh_from_db()
        borrowing2.refresh_from_db()

        res = self.client.get(
            BORROWING_URL, {"users": user2.id}
        )
        serializer_borrowing1 = BorrowingListSerializer(borrowing1)
        serializer_borrowing2 = BorrowingListSerializer(borrowing2)

        self.assertNotIn(serializer_borrowing1.data, res.data["results"])
        self.assertIn(serializer_borrowing2.data, res.data["results"])
