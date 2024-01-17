from django.contrib import admin

from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'text', 'author', 'pub_date', 'cooking_time', 'favorited_num',
    )
    readonly_fields = ('favorited_num',)
    search_fields = ('name', 'author',)
    list_filter = ('name', 'author', 'pub_date', 'ingredients', 'tags',)
    empty_value_display = '-пусто-'

    def favorited_num(self, obj):
        return obj.favorited_num()

    favorited_num.short_description = 'Добавлено в избранное'
