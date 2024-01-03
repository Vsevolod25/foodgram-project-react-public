from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, unique=True , verbose_name='название'
    )
    measurement_unit = models.CharField(
        max_length=10, verbose_name='единицы измерения'
    )

    def __str__(self):
        return self.name
