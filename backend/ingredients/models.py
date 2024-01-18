from django.db import models

from backend.constants import MAX_FIELD_LENGTH


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name='название',
        verbose_name_plural='названия'
    )
    measurement_unit = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name='единицы измерения',
        verbose_name_plural='единицы измерения'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=('name', 'measurement_unit')
            ),
        )
        ordering = ('name', 'measurement_unit',)

    def __str__(self):
        return self.name
