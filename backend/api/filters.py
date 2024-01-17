from django_filters import filters, FilterSet

from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import User
from .functions import get_many_to_many_list


class RecipeFilters(FilterSet):
    author = filters.ModelChoiceField(queryset=User.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, is_favorited):
        if (
            (self.request.user.is_authenticated)
            and (is_favorited is not None)
        ):
            return queryset.filter(
                id__in=get_many_to_many_list(self.request, Favorite)
            )
        return queryset

    def get_is_in_shopping_cart(self, queryset, is_in_shopping_cart):
        if (
            (self.request.user.is_authenticated)
            and (is_in_shopping_cart is not None)
        ):
            return queryset.filter(
                id__in=get_many_to_many_list(self.request, ShoppingCart)
            )
        return queryset
