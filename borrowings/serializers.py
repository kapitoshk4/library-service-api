from rest_framework import serializers

from borrowings.models import Borrowing
from books.serializers import BookSerializer
from borrowings.telegram_helper import send_borrowing_notification
from payments.serializers import PaymentSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date",)

    def validate(self, attrs):
        Borrowing.validate_borrowing(
            attrs["book"].inventory
        )
        return attrs

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        borrowing = Borrowing.objects.create(
            user=self.context["request"].user,
            book=book,
            expected_return_date=validated_data["expected_return_date"]
        )
        send_borrowing_notification(borrowing=borrowing)

        return borrowing


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
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user"
        )


class BorrowingRetrieveSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.CharField(
        source="user.full_name",
        read_only=True
    )
    payments = PaymentSerializer(read_only=True, many=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payments",
        )
