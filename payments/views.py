import stripe
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

from borrowings.telegram_helper import payment_is_paid_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.utils import create_stripe_payment_session


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset


@api_view(["GET"])
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Session ID is required."}, status=400)

    with transaction.atomic():
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            payment = Payment.objects.get(session_id=session_id)
            payment.status = "Paid"
            payment.save()
            payment_is_paid_notification(payment)

            return HttpResponse("Payment was successful. Thank you!")
        else:
            return HttpResponse("Payment not successful. Please try again.")


@api_view(["GET"])
def payment_cancel(request):
    return HttpResponse("Payment was canceled. You can try to pay again within 24 hours.")


@api_view(["POST"])
def payment_renew(request):
    session_id = request.data.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Session ID is required."}, status=400)

    with transaction.atomic():
        payment = Payment.objects.get(session_id=session_id)
        borrowing = payment.borrowing
        payment.delete()

        create_stripe_payment_session(borrowing, request)

        return HttpResponse("Payment session has been renewed successfully.")

