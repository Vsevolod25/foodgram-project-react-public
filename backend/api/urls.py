from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from .functions import download_shopping_cart
from .views import (
    AllSubscriptionsViewSet,
    IngredientViewSet,
    FavoriteViewSet,
    UsersViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    SubscriptionViewSet,
    TagViewSet
)

router_v1 = DefaultRouter()

router_v1.register(
    'users/subscriptions', AllSubscriptionsViewSet, basename='subscriptions'
)
router_v1.register('users', UsersViewSet, basename='users')
router_v1.register(
    r'users/(?P<user_id>\d+)/subscribe',
    SubscriptionViewSet,
    basename='subscribe'
)
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
#router_v1.register(
#    'recipes/download_shopping_cart',
#    download_shopping_cart(),
#    basename='download_shopping_cart'
#)
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavoriteViewSet,
    basename='favorite'
)
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]
