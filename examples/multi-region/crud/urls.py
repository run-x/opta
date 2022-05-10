from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"test_model", views.TestModelViewSet, basename="test_model")


urlpatterns = [path("crud_index", views.crud_index, name="crud_index")]
urlpatterns += router.urls
