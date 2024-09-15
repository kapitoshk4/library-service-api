from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    borrow_date = models.DateTimeField(default=timezone.now)
    expected_return_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["borrow_date", "expected_return_date", "actual_return_date"],
                name="unique_borrowing_dates"
            )
        ]

    @staticmethod
    def validate_borrowing(inventory: int):
        if inventory == 0:
            raise ValidationError(
                {
                    "inventory": f"The book is currently out of stock."
                }
            )

    def clean(self):
        Borrowing.validate_borrowing(
            self.book.inventory
        )

    def __str__(self):
        return f"Borrowing by {self.user} for {self.book} on {self.borrow_date}"
