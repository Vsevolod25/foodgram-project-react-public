from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='название'
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='единицы измерения'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=('name', 'measurement_unit')
            ),
        )

    def __str__(self):
        return self.name
