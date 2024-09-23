from django.urls import path, include
from rest_framework import routers

from payments.views import (
    PaymentViewSet,
    payment_success,
    payment_cancel,
    payment_renew
)

router = routers.DefaultRouter()
router.register("", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("success/", payment_success, name="payment-success"),
    path("cancel/", payment_cancel, name="payment-cancel"),
    path("renew-payment/", payment_renew, name="payment-renew")
]


app_name = "payments"
