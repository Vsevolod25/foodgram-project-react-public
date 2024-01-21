from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import (
    LimitOffsetPagination, PageNumberPagination
)

from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription, User

MODELS_DEPENDENCY_DICT = {
    Subscription: User,
    Favorite: Recipe,
    ShoppingCart: Recipe
}

MODELS_FIELDS_DICT = {
    Subscription: 'subscription',
    Favorite: 'recipe',
    ShoppingCart: 'recipe'
}

ERRORS_NOT_EXISTS_DICT = {
    Subscription: 'Указанная подписка не существует.',
    Favorite: 'Указанного рецепта нет в избранном.',
    ShoppingCart: 'Указанного рецепта нет в корзине.'
}


def get_many_to_many_instance(request, pk, model):
    user = request.user
    obj = get_object_or_404(MODELS_DEPENDENCY_DICT[model], pk=pk)
    instance = model.objects.filter(
        **{'user': user, MODELS_FIELDS_DICT[model]: obj}
    )
    if not instance.exists():
        raise ValidationError(ERRORS_NOT_EXISTS_DICT[model])
    return instance


def get_many_to_many_list(request, model):
    return [
        model_to_dict(obj)[
            MODELS_FIELDS_DICT[model]
        ] for obj in model.objects.filter(user=request.user)
    ]

def get_pagination_class(self):
    limit = self.request.query_params.get('limit')
    if limit:
        return LimitOffsetPagination
    return PageNumberPagination
