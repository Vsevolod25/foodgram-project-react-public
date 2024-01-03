from django.db import models


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='название'
    )
    color = models.CharField(max_length=7, verbose_name='цвет')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='слаг')

    def __str__(self):
        return self.name
