from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view
from books.models import Book
from books.permissions import IsAdminAllOrAuthenticatedReadOnly
from books.serializers import BookSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Retrieve list of books",
        description="Retrieve a list of all books. Authenticated users can view the list, while admins have full access.",
        responses={200: BookSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Retrieve a single book",
        description="Retrieve the details of a specific book by its ID. Authenticated users can view book details, while admins can perform all actions.",
        responses={200: BookSerializer}
    ),
    create=extend_schema(
        summary="Create a new book",
        description="Admins can create a new book record.",
        request=BookSerializer,
        responses={201: BookSerializer}
    ),
    update=extend_schema(
        summary="Update an existing book",
        description="Admins can update an existing book's details.",
        request=BookSerializer,
        responses={200: BookSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update an existing book",
        description="Admins can partially update a book's details.",
        request=BookSerializer,
        responses={200: BookSerializer}
    ),
    destroy=extend_schema(
        summary="Delete a book",
        description="Admins can delete a book by its ID.",
        responses={204: None}
    )
)
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminAllOrAuthenticatedReadOnly,)
