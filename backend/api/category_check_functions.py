from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription, User


def favorite_check(user, recipe):
    return False


def shopping_cart_check(user, recipe):
    return False


def subscription_check(user, subscription):
    return False
