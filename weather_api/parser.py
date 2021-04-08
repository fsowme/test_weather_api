import concurrent.futures
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

from pydantic_models import OWCurrent, OWDaily, OWHourly, WBCities, WBCurrent

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_api.settings")
API_KEY = os.getenv("API_WEATHERBIT")
django.setup()


# pylint: disable=wrong-import-position
from weather.models import City, Country, Source, Weather

OW_CITIES = "http://bulk.openweathermap.org/sample/city.list.min.json.gz"
WB_CITIES = "https://www.weatherbit.io/static/exports/cities_20000.json.gz"
OW_FORECAST_16_DAYS = "http://bulk.openweathermap.org/sample/daily_14.json.gz"
OW_FORECAST_5_DAYS = "http://bulk.openweathermap.org/sample/hourly_14.json.gz"
OW_CURRENT = "http://bulk.openweathermap.org/sample/weather_14.json.gz"
WB_CURRENT = "https://api.weatherbit.io/v2.0/current?city={}&country={}&key={}"

OPENWEATHER = Source.objects.get(name="OpenWeather")
WEATHERBIT = Source.objects.get(name="WeatherBit")

logger = logging.getLogger(__name__)


class Downloader:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_data(self):
        pass


class DownloaderGz(Downloader):
    def __init__(self, url, data=None):
        self.url = url
        self.data = data

    def get_data(self):
        response = requests.get(self.url)
        compressed = io.BytesIO(response.content)
        uncompressed = gzip.GzipFile(fileobj=compressed)
        self.data = uncompressed


class DownloaderCity(DownloaderGz):
    def from_json(self):
        if self.data:
            cities = self.data.read()
            self.data.seek(0)
            return json.loads(cities)
        raise LookupError("Data not load")


class OWDownloaderWeather(DownloaderGz):
    def from_json(self):
        if self.data:
            return [json.loads(line) for line in self.data]
        raise LookupError("Data not load")


class WBDownloaderWeather(DownloaderGz):
    def get_data(self):
        response = requests.get(self.url)
        self.data = response.content
        return self.data

    def from_json(self):
        if self.data:
            return [json.loads(line) for line in self.data]
        raise LookupError("Data not load")


class Saver:
    __metaclass__ = ABCMeta

    @abstractmethod
    def create(self):
        pass


class WeatherCitySaver(Saver):
    def __init__(self, weather_data, scheme, source):
        self.weather_data = weather_data
        self.scheme = scheme
        self.source = source

    @staticmethod
    def get_city_data(data):
        return (
            data.city.name,
            data.city.country,
            data.city.coord.lat,
            data.city.coord.lon,
        )

    def get_or_create_city(self, name, country_name, latitude, longitude):
        country, _ = Country.objects.get_or_create(name=country_name)
        return City.objects.get_or_create(
            name=name,
            country=country,
            latitude=latitude,
            longitude=longitude,
            source=self.source,
        )

    def create_weather(self, data, city):
        for weather in data.data:
            date = make_aware(datetime.fromtimestamp(weather.dt))
            temperature = weather.temp.temp
            if not Weather.objects.filter(city=city, date=date).exists():
                Weather.objects.create(
                    city=city,
                    date=date,
                    temperature=temperature,
                    source=self.source,
                )

    def create(self):
        for city_weather in self.weather_data:
            try:
                weather = self.scheme(**city_weather)
            except ValidationError as error:
                logger.warning("Invalid data on %s: %s`", city_weather, error)
            else:
                name, country_name, lat, lon = self.get_city_data(weather)
                city, _ = self.get_or_create_city(name, country_name, lat, lon)
                self.create_weather(data=weather, city=city)


class WBSaverCurrent(WeatherCitySaver):
    def __init__(self, weather_data, scheme=WBCurrent, source=WEATHERBIT):
        super().__init__(weather_data, scheme, source)

    @staticmethod
    def get_city_data(data):
        return (
            data.data[0].name,
            data.data[0].country,
            data.data[0].lat,
            data.data[0].lon,
        )

    def create_weather(self, data, city):
        temperature = data.data[0].temp + 273.15
        date = make_aware(datetime.fromtimestamp(data.data[0].date))
        weather, now_created = Weather.objects.get_or_create(
            city=city,
            date=date,
            defaults={"temperature": temperature, "source": self.source},
        )
        if not now_created and weather.temperature != temperature:
            weather.temperature = temperature
            weather.save()


class WBSaverCity(Saver):
    def __init__(self, cities_data, scheme=WBCities, source=WEATHERBIT):
        self.cities_data = cities_data
        self.scheme = scheme
        self.source = source

    def create(self):
        for city_data in self.cities_data:
            try:
                city = WBCities(**city_data)
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
                        source=self.source,
                    )


class OWSaverCurrent(WeatherCitySaver):
    def __init__(self, weather_data, scheme=OWCurrent, source=OPENWEATHER):
        super().__init__(weather_data, scheme, source)

    def create_weather(self, data, city):
        temperature = data.data.temp
        date = make_aware(datetime.fromtimestamp(data.dt))
        weather, now_created = Weather.objects.get_or_create(
            city=city,
            date=date,
            defaults={"temperature": temperature, "source": self.source},
        )
        if not now_created and weather.temperature != temperature:
            weather.temperature = temperature
            weather.save()


class OWSaverDaily(WeatherCitySaver):
    def __init__(self, weather_data, scheme=OWDaily, source=OPENWEATHER):
        super().__init__(weather_data, scheme, source)


class OWSaverHourly(WeatherCitySaver):
    def __init__(self, weather_data, scheme=OWHourly, source=OPENWEATHER):
        super().__init__(weather_data, scheme, source)


def get_wb_weather(cities, pattern_url, data_downloader, key=None):
    key = API_KEY if key is None else key
    responses = []
    cities_values = cities.values_list("name", "country__name")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for city_name, country_name in cities_values:
            url = pattern_url.format(city_name, country_name, key)
            downloader = data_downloader(url)
            responses.append(executor.submit(downloader.get_data))
    return [json.loads(response.result()) for response in responses]


if __name__ == "__main__":

    weather_downloader = WBDownloaderWeather(OW_FORECAST_16_DAYS)
    weather_downloader.get_data()
    OWSaverDaily(weather_downloader.from_json()[:5]).create()

    weather_downloader = OWDownloaderWeather(OW_FORECAST_5_DAYS)
    weather_downloader.get_data()
    OWSaverHourly(weather_downloader.from_json()[:7]).create()

    weather_downloader = OWDownloaderWeather(OW_CURRENT)
    weather_downloader.get_data()
    OWSaverCurrent(weather_downloader.from_json()[:20]).create()

    cities_downloader = DownloaderCity(WB_CITIES)
    cities_downloader.get_data()
    WBSaverCity(cities_downloader.from_json()[:40]).create()
    cities_qs = City.objects.filter(source__pk=2)[15:20]
    wb_data = get_wb_weather(
        cities_qs, WB_CURRENT, WBDownloaderWeather, API_KEY
    )
    WBSaverCurrent(wb_data).create()
