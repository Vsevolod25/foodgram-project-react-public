from django.contrib import admin

from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'text', 'author', 'pub_date', 'cooking_time',
    )
    search_fields = ('name', 'author',)
    list_filter = ('pub_date', 'ingredients', 'tags',)
    empty_value_display = '-пусто-'
