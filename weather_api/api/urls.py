from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register("weather", views.WeatherViewSet, basename="weather")


urlpatterns = [
    path("front/", include(router.urls)),
]
