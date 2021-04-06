import json
from datetime import datetime

from django.http.response import HttpResponse

from weather.models import City, Weather


def weather_test(request):
    return HttpResponse("Weather ok")


def get_weather(request):
    myfile = open("weather_14.json")
    city_data = json.loads(myfile.readline())

    myfile.close()
    city = City.objects.create(
        name=city_data["city"]["name"],
        latitude=city_data["city"]["coord"]["lat"],
        longitude=city_data["city"]["coord"]["lon"],
    )
    date = datetime.fromtimestamp(city_data["time"])
    weather = Weather.objects.create(
        city=city, date=date, temperature=city_data["main"]["temp"]
    )
    return HttpResponse(f"{weather.temperature} in {city.name}")
