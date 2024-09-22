import stripe
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework import status

from borrowings.telegram_helper import payment_is_paid_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.utils import create_stripe_payment_session


@extend_schema_view(
    list=extend_schema(
        summary="Retrieve list of payments",
        description="Retrieve a list of all payments. Non-staff users can only view their own payments.",
        responses={200: PaymentSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Retrieve a single payment",
        description="Retrieve details of a specific payment by its ID. Non-staff users can only view their own payments.",
        responses={200: PaymentSerializer}
    ),
    create=extend_schema(
        summary="Create a new payment",
        description="Admins can create a new payment entry.",
        request=PaymentSerializer,
        responses={201: PaymentSerializer}
    ),
    update=extend_schema(
        summary="Update an existing payment",
        description="Admins can update an existing payment record.",
        request=PaymentSerializer,
        responses={200: PaymentSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update an existing payment",
        description="Admins can partially update a payment's details.",
        request=PaymentSerializer,
        responses={200: PaymentSerializer}
    ),
    destroy=extend_schema(
        summary="Delete a payment",
        description="Admins can delete a payment by its ID.",
        responses={204: None}
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)

        return queryset


@extend_schema(
    summary="Handle successful payment",
    description="Endpoint to handle a successful payment via Stripe. Updates the payment status to 'Paid' and sends a notification.",
    parameters=[
        {
            "name": "session_id",
            "in": "query",
            "description": "The session ID from the Stripe payment",
            "required": True,
            "schema": {"type": "string"}
        }
    ],
    responses={
        200: {"description": "Payment was successful. Thank you!"},
        400: {"description": "Session ID is required or invalid."}
    }
)
@api_view(["GET"])
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Session ID is required."}, status=400)

    with transaction.atomic():
        session = stripe.checkout.Session.retrieve(session_id)

        if session["payment_status"] == "paid":
            payment = Payment.objects.get(session_id=session_id)
            payment.status = "Paid"
            payment.save()
            payment_is_paid_notification(payment)

            return HttpResponse("Payment was successful. Thank you!")
        else:
            return HttpResponse("Payment not successful. Please try again.")


@extend_schema(
    summary="Handle canceled payment",
    description="Endpoint to handle a canceled payment. Displays a message to the user.",
    responses={
        200: {"description": "Payment was canceled. You can try to pay again within 24 hours."}
    }
)
@api_view(["GET"])
def payment_cancel(request):
    return HttpResponse("Payment was canceled. You can try to pay again within 24 hours.")


@extend_schema(
    summary="Renew a payment session",
    description="Endpoint to renew an existing Stripe payment session. Deletes the previous payment and creates a new one.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The Stripe session ID of the expired payment."
                }
            },
            "required": ["session_id"]
        }
    },
    responses={
        200: {"description": "Payment session has been renewed successfully."},
        400: {"description": "Session ID is required or invalid."}
    }
)
@api_view(["POST"])
def payment_renew(request):
    session_id = request.data.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Session ID is required."}, status=400)

    with transaction.atomic():
        payment = Payment.objects.get(session_id=session_id)
        borrowing = payment.borrowing
        payment.delete()

        create_stripe_payment_session(borrowing, request, total_price=borrowing.total_price)

        return HttpResponse("Payment session has been renewed successfully.")
