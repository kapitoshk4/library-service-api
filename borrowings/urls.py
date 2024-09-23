from django.urls import path, include
from rest_framework import routers

from borrowings.views import BorrowingViewSet

router = routers.DefaultRouter()
router.register("", BorrowingViewSet)

urlpatterns = router.urls

app_name = "borrowings"
