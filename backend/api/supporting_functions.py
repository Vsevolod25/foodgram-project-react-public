from django.shortcuts import get_object_or_404

from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription, User


def get_recipe(self):
    return get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))


def get_user(self):
    return get_object_or_404(User, pk=self.kwargs.get('user_id'))


def favorite_check(user, recipe):
    return False


def shopping_cart_check(user, recipe):
    return False


def subscription_check(user, subscription):
    return False
