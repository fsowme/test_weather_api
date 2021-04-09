# Тестовое для АО "НПО "Эшелон"

## Описание
Данные о погоде с сайта openweather берутся из примеров bulk файлов, с сайта 
weatherbit сначало скачивается список городов, после этого через api запрашивается погода для этих городов. Запросы к api weatherbit отправляются асинхронно (с асинхронностью раньше дела не имел, хотя тема мне интересна). Для проверки и парсинга json использовал pydantic, тут тоже первый опыт :)

Основные файлы:
- parser.py
- pydantic_models.py
- weather/models.py

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



