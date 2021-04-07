from django.db import models


class Source(models.Model):
    url = models.URLField(verbose_name="URL", max_length=200, unique=True)
    name = models.CharField(
        verbose_name="Data source name", max_length=200, unique=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Data source"
        verbose_name_plural = "Data sources"

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(verbose_name="Country", max_length=2, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(verbose_name="City name", max_length=200)
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    country = models.ForeignKey(
        Country, models.CASCADE, verbose_name="Country", related_name="cities"
    )
    source = models.ForeignKey(
        Source, models.CASCADE, verbose_name="Country", related_name="cities"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "City"
        verbose_name_plural = "Cities"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "latitude", "longitude"],
                name="%(app_label)s_%(class)s_check_fields_unique",
            )
        ]

    def __str__(self):
        return self.name


class Weather(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name="City",
        related_name="weather",
    )
    date = models.DateTimeField(verbose_name="Weather date")
    temperature = models.FloatField(verbose_name="Temperature")
    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        verbose_name="Weather data source",
        related_name="weather",
    )

    class Meta:
        ordering = ["city", "date"]
        verbose_name = "Weather"
        verbose_name_plural = "Weather"
        constraints = [
            models.UniqueConstraint(
                fields=["city", "date"],
                name="%(app_label)s_%(class)s_check_fields_unique",
            )
        ]

    def __str__(self):
        return f"Weather in {self.city.name} ({self.city.pk})"
