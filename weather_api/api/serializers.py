from rest_framework import serializers
from weather.models import City, Source, Weather


class WeatherSerializer(serializers.ModelSerializer):
    temperature = serializers.FloatField()
    date = serializers.DateTimeField()
    city = serializers.SlugRelatedField(
        queryset=City.objects.all(), slug_field="name"
    )
    source = serializers.SlugRelatedField(
        queryset=Source.objects.all(), slug_field="name"
    )

    class Meta:
        model = Weather
        fields = "__all__"
