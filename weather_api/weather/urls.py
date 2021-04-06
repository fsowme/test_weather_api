from django.urls import path

from weather import views

urlpatterns = [
    path("", views.weather_test, name="weather_test"),
    path("get_14/", views.get_weather, name="get_weather"),
]
