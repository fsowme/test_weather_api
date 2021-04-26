# Тестовое для АО "НПО "Эшелон"

## Описание
Данные о погоде с сайта openweather берутся из примеров bulk файлов, с сайта 
weatherbit сначало скачивается список городов, после этого через api запрашивается погода для этих городов. Запросы к api weatherbit отправляются асинхронно (с асинхронностью раньше дела не имел, хотя тема мне интересна). Для проверки и парсинга json использовал pydantic, тут тоже первый опыт :)

Основные файлы:
- [parser.py](https://github.com/fsowme/test_echelon_weather_api/blob/master/weather_api/parser.py)
    - class DownloaderGz(Downloader) - родительский класс загрузчиков архивов с данными
        1. class DownloaderCity(DownloaderGz) - загрузчик доступных городов
        2.  class OWDownloaderWeather(DownloaderGz) - загрузчик погоды с сайта OpenWeather
        3. class WBDownloaderWeather(DownloaderGz) - загрузчик погоды с сайта WeatherBit
    - class WeatherCitySaver(Saver) - родительский класс для сохранения данных по погоде в базе. Методы:
        1. def get_city_data(data) - возвращает данные городов в правильном виде, переопределяется для каждого источника
        2. def get_or_create_city - возвращает из базы или создаёт в базе город (общий для всех источников данных, тк get_city_data подготовит данные)
        3. def create_weather - создаёт объект погоды в базе (переопределяется для разныех источников данных погоды)
        4. def create - десериализирует данные и вызывает метод create_weather. Не переопределяется для классов сохранения погоды
    - class WBSaverCurrent(WeatherCitySaver) - сохраняет текущую погоду с WeatherBit
    - class OWSaverCurrent(WeatherCitySaver) - сохраняет текущую погоду с OpenWeather
    - class OWSaverDaily(WeatherCitySaver) - сохраняет погоду по дням с OpenWeather
    - class OWSaverHourly(WeatherCitySaver) - сохраняет погоду по часам с OpenWeather


- [pydantic_models.py](https://github.com/fsowme/test_echelon_weather_api/blob/master/weather_api/pydantic_models.py) - первое знакомство с pydantic
- [weather/models.py](https://github.com/fsowme/test_echelon_weather_api/blob/master/weather_api/weather/models.py) - модели Django

В api один endpoint для получения погоды (возвращается весь список), можно через параметр передать имя города. Включена стандартная пагинация drf. В ответе указан источник информации о погоде. API в отдельном приложение.


## Запуск
```
git clone git@github.com:fsowme/test_echelon_weather_api.git
cd test_echelon_weather_api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pip install --upgrade pip
touch .env && nano .env
```
#### Наполнение .env
```
SECRET_KEY= Секретный ключ django
DB_ENGINE="django.db.backends.postgresql" 
POSTGRES_DB="weather_db"
DB_HOST="localhost"
DB_PORT="5432"
POSTGRES_USER="weather_user"
POSTGRES_PASSWORD="weather_pass"
API_WEATHERBIT= api key от weatherbit
```
#### Что бы сгенерировать secret key можно использовать встроенную функцию django
```
python weather_api/manage.py shell -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
#### запуск postgresql:
```
sudo docker-compose up -d
```
#### Подготовка django
```
cd weather_api
python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser

python manage.py shell -c 'from weather.models import Source; Source.objects.create(name="OpenWeather", url="https://openweathermap.org"); Source.objects.create(name="WeatherBit", url="https://www.weatherbit.io")'
```

#### Получение данных
- с openweather будут загружены в память примеры bulk файлов
- распакованы из gz и созданы объекты моделей из json (города и погода)
- с weatherbit в память будет загружен файл с городами, которые запишутся в бд
- к api weatherbit будут асинхронно отправлены запросы на получение данных о погоде
```
python parser.py
```

#### Запуск django
- эндпоинт для получения погоды 127.0.0.1:8000/api/front/weather/
- в query можно передать начало имени города, например query_param=Mosc \
    вернёт погоду во всех городах именя которых начинается на "Mosc"

```
python manage.py runserver
```



