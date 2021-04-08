from rest_framework import viewsets
from weather.models import Weather

from api.serializers import WeatherSerializer


class WeatherViewSet(viewsets.ModelViewSet):
    serializer_class = WeatherSerializer
    queryset = Weather.objects.all()
