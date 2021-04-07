import gzip
import io
import json
import logging
import os
from abc import ABCMeta, abstractmethod
from datetime import datetime

import django
import requests
from django.utils.timezone import make_aware
from dotenv import load_dotenv
from pydantic import ValidationError

from pydantic_models import (
    OpenWeatherCurrent,
    OpenWeatherDaily,
    OpenWeatherHourly,
    WeatherBitCities,
)

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_api.settings")
API_KEY = os.getenv("API_WEATHERBIT")
django.setup()


# pylint: disable=wrong-import-position
from weather.models import City, Country, Source, Weather

OPENWEATHER_CITIES = (
    "http://bulk.openweathermap.org/sample/city.list.min.json.gz"
)
WEATHERBIT_CITIES = (
    "https://www.weatherbit.io/static/exports/cities_20000.json.gz"
)
OPENWEATHER_FORECAST_16_DAYS = (
    "http://bulk.openweathermap.org/sample/daily_14.json.gz"
)
OPENWEATHER_FORECAST_5_DAYS = (
    "http://bulk.openweathermap.org/sample/hourly_14.json.gz"
)
OPENWEATHER_CURRENT = (
    "http://bulk.openweathermap.org/sample/weather_14.json.gz"
)
WEATHERBIT_URL = "https://api.weatherbit.io/v2.0"
WEATHERBIT_CURRENT = (
    "https://api.weatherbit.io/v2.0"
    "/current?city={}&country={}&key=27b8277ce8564624847198a0d46e0538"
)

logger = logging.getLogger(__name__)


class Downloader:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_data(self):
        pass


class BulkGzDownloader(Downloader):
    def __init__(self, url, data=None):
        self.url = url
        self.data = data

    def get_data(self):
        response = requests.get(self.url)
        compressed = io.BytesIO(response.content)
        uncompressed = gzip.GzipFile(fileobj=compressed)
        self.data = uncompressed


class CityDownloader(BulkGzDownloader):
    def from_json(self):
        if self.data:
            cities = self.data.read()
            self.data.seek(0)
            return json.loads(cities)
        raise LookupError("Data not load")


class WeatherDownloader(BulkGzDownloader):
    def from_json(self):
        if self.data:
            return [json.loads(line) for line in self.data]
        raise LookupError("Data not load")


class Saver:
    __metaclass__ = ABCMeta

    @abstractmethod
    def create(self):
        pass


class CitySaver(Saver):
    SOURCE = Source.objects.get(name="WeatherBit")

    def __init__(self, cities_data):
        self.cities_data = cities_data

    def create(self):
        for city_data in self.cities_data:
            try:
                city = WeatherBitCities(**city_data)
            except ValidationError as error:
                logger.warning("Invalid data on %s: %s", city_data, error)
            else:
                country, _ = Country.objects.get_or_create(name=city.country)
                if not City.objects.filter(
                    name=city.name, latitude=city.lat, longitude=city.lon
                ).exists():
                    City.objects.create(
                        name=city.name,
                        country=country,
                        latitude=city.lat,
                        longitude=city.lon,
                        source=self.SOURCE,
                    )


class WeatherBitSaver(Saver):
    CITIES = City.objects.filter(source__name="WeatherBit")

    def __init__(self):
        self.weather = []

    def get_weather(self):
        for city in self.CITIES:
            # print(WEATHERBIT_CURRENT.format(city.name, city.country.name))
            response = requests.get(
                WEATHERBIT_CURRENT.format(city.name, city.country.name)
            )

    def create(self):
        pass


class OpenWeatherSaver(Saver):
    SOURCE = Source.objects.get(name="OpenWeather")

    def __init__(self, weather_data, data_scheme):
        self.weather_data = weather_data
        self.data_scheme = data_scheme

    @staticmethod
    def get_city_data(data):
        return (
            data.city.name,
            data.city.country,
            data.city.coord.lat,
            data.city.coord.lon,
        )

    @classmethod
    def get_or_create_city(cls, name, country_name, latitude, longitude):
        country, _ = Country.objects.get_or_create(name=country_name)
        return City.objects.get_or_create(
            name=name,
            country=country,
            latitude=latitude,
            longitude=longitude,
            source=cls.SOURCE,
        )

    @classmethod
    def create_weather(cls, data, city):
        for weather in data.data:
            date = make_aware(datetime.fromtimestamp(weather.dt))
            temperature = weather.temp.temp
            if not Weather.objects.filter(city=city, date=date).exists():
                Weather.objects.create(
                    city=city,
                    date=date,
                    temperature=temperature,
                    source=cls.SOURCE,
                )

    def create(self):
        for city_weather in self.weather_data:
            try:
                weather = self.data_scheme(**city_weather)
            except ValidationError as error:
                logger.warning("Invalid data on %s: %s`", city_weather, error)
            else:
                name, country_name, lat, lon = self.get_city_data(weather)
                city, _ = self.get_or_create_city(name, country_name, lat, lon)
                self.create_weather(data=weather, city=city)


class OpenWeatherSaverCurrent(OpenWeatherSaver):
    def __init__(self, weather_data, data_scheme=OpenWeatherCurrent):
        super().__init__(weather_data, data_scheme)

    @classmethod
    def create_weather(cls, data, city):
        temperature = data.data.temp
        date = make_aware(datetime.fromtimestamp(data.dt))
        weather, now_created = Weather.objects.get_or_create(
            city=city,
            date=date,
            defaults={"temperature": temperature, "source": cls.SOURCE},
        )
        if not now_created and weather.temperature != temperature:
            weather.temperature = temperature
            weather.save()


class DailyOpenWeatherSaver(OpenWeatherSaver):
    def __init__(self, weather_data, data_scheme=OpenWeatherDaily):
        super().__init__(weather_data, data_scheme)


class HourlyOpenWeatherSaver(OpenWeatherSaver):
    def __init__(self, weather_data, data_scheme=OpenWeatherHourly):
        super().__init__(weather_data, data_scheme)


def main():

    # weather_downloader = WeatherDownloader(OPENWEATHER_FORECAST_16_DAYS)
    # weather_downloader.get_data()
    # DailyOpenWeatherSaver(weather_downloader.from_json()[:5]).create()

    # print("*********************************")
    # weather_downloader = WeatherDownloader(OPENWEATHER_FORECAST_5_DAYS)
    # weather_downloader.get_data()
    # HourlyOpenWeatherSaver(weather_downloader.from_json()[:7]).create()
    # print("*********************************")

    # weather_downloader = WeatherDownloader(OPENWEATHER_CURRENT)
    # weather_downloader.get_data()
    # OpenWeatherSaverCurrent(weather_downloader.from_json()[:20]).create()

    # cities_downloader = CityDownloader(WEATHERBIT_CITIES)
    # cities_downloader.get_data()
    # CitySaver(cities_downloader.from_json()[:10]).create()
    WeatherBitSaver().get_weather()


if __name__ == "__main__":
    main()
