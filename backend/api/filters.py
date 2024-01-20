from django_filters import CharFilter, filters, FilterSet

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, ShoppingCart


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return Favorite.objects.filter(
                user=self.request.user
            ).values('recipe')
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=self.request.user
            ).values('recipe')
        return queryset
