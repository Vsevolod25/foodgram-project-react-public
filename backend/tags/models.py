from colorfield.fields import ColorField
from django.db import models

from backend.constants import MAX_FIELD_LENGTH


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='название'
    )
    color = ColorField(
        max_length=7,
        unique=True,
        verbose_name='цвет'
    )
    slug = models.SlugField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name='Тег'
        verbose_name_plural='Теги'

    def __str__(self):
        return self.name
