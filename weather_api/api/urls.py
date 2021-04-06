from django.urls import path
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()

urlpatterns = [path("front/", views.api_test, name="api_test")]
