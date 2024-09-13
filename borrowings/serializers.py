from rest_framework import serializers

from borrowings.models import Borrowing
from books.serializer import BookSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "actual_return_date", "book", "user",)


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(
        source="book.title",
        read_only=True
    )
    user = serializers.CharField(
        source="user.full_name",
        read_only=True
    )

    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "actual_return_date", "book", "user",)


class BorrowingRetrieveSerializer(BorrowingSerializer):
    book = BookSerializer()
    user = serializers.CharField(
        source="user.full_name",
        read_only=True
    )
