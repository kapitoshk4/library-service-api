from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingListSerializer, BorrowingRetrieveSerializer
from payments.utils import create_stripe_payment_session


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _params_to_int(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.action == "list":
            serializer_class = BorrowingListSerializer
        if self.action == "retrieve":
            serializer_class = BorrowingRetrieveSerializer

        return serializer_class

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

    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)
        create_stripe_payment_session(borrowing)

    @action(detail=True, methods=["POST"], url_path="return")
    def return_borrowing(self, request, pk=None):
        with transaction.atomic():
            borrowing = self.get_object()
            if borrowing.actual_return_date:
                return Response({"error": "Book already returned"}, status.HTTP_400_BAD_REQUEST)

            borrowing.actual_return_date = timezone.now()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            return Response({"status": "Book returned"}, status.HTTP_200_OK)
