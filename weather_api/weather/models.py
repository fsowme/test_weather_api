from django.db import models


class City(models.Model):
    name = models.CharField(verbose_name="City name", max_length=200)
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    country = models.CharField(verbose_name="Country", max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name = "City"
        verbose_name_plural = "Cities"
        constraints = [
            models.UniqueConstraint(
                fields=["latitude", "longitude"],
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
    temperature = models.SmallIntegerField(verbose_name="Temperature")

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
