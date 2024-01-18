from colorfield.fields import ColorField
from django.db import models

from backend.constants import MAX_FIELD_LENGTH


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='название',
        verbose_name_plural='названия'
    )
    color = ColorField(
        max_length=7,
        unique=True,
        verbose_name='цвет',
        verbose_name_plural='цвета'
    )
    slug = models.SlugField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='слаг',
        verbose_name_plural='слаги'
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
