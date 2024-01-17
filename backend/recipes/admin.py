from django.contrib import admin

from .models import (
    Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
)


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


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('favorite',)
    search_fields = ('favorite__name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('shopping_cart',)
    search_fields = ('shopping_cart__name',)


admin.site.register(RecipeIngredient)
admin.site.register(RecipeTag)
