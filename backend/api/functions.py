from io import BytesIO

from django.forms.models import model_to_dict
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription, User

MODELS_DEPENDENCY_DICT = {
    Subscription: User,
    Favorite: Recipe,
    ShoppingCart: Recipe
}

MODELS_FIELDS_DICT = {
    Subscription: 'subscription',
    Favorite: 'favorite',
    ShoppingCart: 'shopping_cart'
}

ERRORS_NOT_EXISTS_DICT = {
    Subscription: 'Указанная подписка не существует.',
    Favorite: 'Указанного рецепта нет в избранном.',
    ShoppingCart: 'Указанного рецепта нет в корзине.'
}


def add_recipe_to_category_validation(self, model):
    user = self.request.user
    if Recipe.objects.filter(pk=self.kwargs.get('recipe_id')).exists():
        obj = Recipe.objects.get(pk=self.kwargs.get('recipe_id'))
    else:
        raise ValidationError('Указанного рецепта не существует.')
    if model.objects.filter(
        **{'user': user, MODELS_FIELDS_DICT[model]: obj}
    ).exists():
        raise ValidationError('Нельзя повторно добавлять рецепт в корзину.')
    return obj


def create_shopping_cart_txt():
    return ''


def download_shopping_cart():
    buffer = BytesIO()
    shopping_cart = create_shopping_cart_txt()
    shopping_cart.save(buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'shopping_cart.txt')


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
