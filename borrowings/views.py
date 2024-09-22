from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingListSerializer, BorrowingRetrieveSerializer
from payments.utils import create_stripe_payment_session


@extend_schema_view(
    list=extend_schema(
        summary="Retrieve list of borrowings",
        description="Retrieve a list of borrowings with optional filters for active status and users.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter by active borrowings (true/false)",
                required=False,
                type=str,
                enum=["true", "false"]
            ),
            OpenApiParameter(
                name="users",
                description="Comma-separated list of user IDs (staff only)",
                required=False,
                type=str
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Retrieve a single borrowing",
        description="Retrieve details of a specific borrowing by its ID.",
    ),
    create=extend_schema(
        summary="Create a new borrowing",
        description="Create a new borrowing for the authenticated user, triggering a Stripe payment session.",
        request=BorrowingSerializer,
        responses={201: BorrowingSerializer}
    ),
    update=extend_schema(
        summary="Update an existing borrowing",
        description="Update a borrowing record. Only staff can perform this action.",
        request=BorrowingSerializer,
        responses={200: BorrowingSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update an existing borrowing",
        description="Partially update a borrowing record. Only staff can perform this action.",
        request=BorrowingSerializer,
        responses={200: BorrowingSerializer}
    ),
    destroy=extend_schema(
        summary="Delete a borrowing",
        description="Delete a borrowing record by its ID. Only staff can perform this action.",
        responses={204: None}
    )
)
class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    @staticmethod
    def _params_to_int(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingRetrieveSerializer
        return BorrowingSerializer

    def get_queryset(self):
        queryset = self.queryset
        is_active = self.request.query_params.get("is_active")
        users = self.request.query_params.get("users")
        queryset = queryset.select_related("user", "book").prefetch_related("payments")

        if is_active:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if users and self.request.user.is_staff:
            user_ids = self._params_to_int(users)
            queryset = queryset.filter(user__id__in=user_ids)

        return queryset

    @extend_schema(
        summary="Create a new borrowing",
        description="Create a borrowing and generate a Stripe payment session.",
        responses={201: BorrowingSerializer}
    )
    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)
        create_stripe_payment_session(borrowing, self.request, total_price=borrowing.total_price)

    @extend_schema(
        summary="Mark borrowing as returned",
        description="Mark a borrowing as returned by setting the actual return date. Increases book inventory by 1.",
        responses={200: OpenApiParameter(description="Book returned", name="book")},
        request=None,
    )
    @action(detail=True, methods=["POST"], url_path="return")
    def return_borrowing(self, request, pk=None):
        with transaction.atomic():
            borrowing = self.get_object()
            if borrowing.actual_return_date:
                return Response({"error": "Book already returned"}, status=status.HTTP_400_BAD_REQUEST)

            borrowing.actual_return_date = timezone.now()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            return Response({"status": "Book returned"}, status=status.HTTP_200_OK)
