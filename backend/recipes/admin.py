from django.contrib import admin

from ingredients.models import Ingredient
from tags.models import Tag
from .models import (
    Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
)


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    min_num = 1


class TagInline(admin.TabularInline):
    model = Recipe.tags.through
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'text', 'author', 'pub_date', 'cooking_time', 'favorited_num',
    )
    readonly_fields = ('favorited_num',)
    search_fields = ('name', 'author',)
    list_filter = ('name', 'author', 'pub_date', 'ingredients', 'tags',)
    empty_value_display = '-пусто-'
    inlines = (IngredientInline, TagInline,)

    def favorited_num(self, obj):
        return obj.favorited_num()

    favorited_num.short_description = 'Добавлено в избранное'


admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeTag)
