from rest_framework import viewsets

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingListSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.action == "list":
            serializer_class = BorrowingListSerializer

        return serializer_class
