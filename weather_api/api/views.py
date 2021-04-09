from rest_framework import viewsets
from weather.models import Weather

from api.serializers import WeatherSerializer


class WeatherViewSet(viewsets.ModelViewSet):
    serializer_class = WeatherSerializer

    def get_queryset(self):
        if query := self.request.query_params.get("query"):
            return Weather.objects.filter(city__name__istartswith=query)
        return Weather.objects.all()

    # lookup_field = "city__name"
