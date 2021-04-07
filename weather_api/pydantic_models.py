from pydantic import BaseModel  # pylint: disable=no-name-in-module


class Temp(BaseModel):
    temp: float

    class Config:
        fields = {"temp": "day"}


class TempDay(BaseModel):
    temp: float


class Coordinates(BaseModel):
    lon: float
    lat: float


class CityData(BaseModel):
    name: str
    coord: Coordinates
    country: str


class WeatherByDay(BaseModel):
    dt: int
    temp: Temp


class WeatherByHour(BaseModel):
    dt: int
    temp: TempDay

    class Config:
        fields = {"temp": "main"}


class OpenWeatherDaily(BaseModel):
    city: CityData
    data: list[WeatherByDay]


class OpenWeatherHourly(BaseModel):
    city: CityData
    data: list[WeatherByHour]


class OpenWeatherCurrent(BaseModel):
    city: CityData
    data: TempDay
    dt: int

    class Config:
        fields = {"data": "main", "dt": "time"}


class WeatherBitCities(BaseModel):
    name: str
    lat: float
    lon: float
    country: str

    class Config:
        fields = {"name": "city_name", "country": "country_code"}
