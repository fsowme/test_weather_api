from django.contrib import admin

from weather.models import City, Country, Source, Weather


admin.site.register(City)
admin.site.register(Country)
admin.site.register(Source)
admin.site.register(Weather)
