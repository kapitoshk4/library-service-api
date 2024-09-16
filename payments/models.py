from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending"
        PAID = "Paid"

    class Type(models.TextChoices):
        PAYMENT = "Payment"
        FINE = "Fine"

    status = models.CharField(choices=Status.choices, max_length=7)
    type = models.CharField(choices=Type.choices, max_length=7)
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE, related_name="payments")
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return f"{self.borrowing} - {self.money_to_pay} {self.status}"
