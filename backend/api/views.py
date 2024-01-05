from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters, viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User
from .mixins import (
    CreateDestroyViewSet, ListCreateDestroyViewSet, ListRetrieveViewSet
)
from .serializers import (
    IngredientSerializer,
    FavoriteSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer
)
from .supporting_functions import get_recipe, get_user


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ('get', 'head', 'post', 'patch', 'delete')
    order_by = ('pub_date', 'name',)


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SubscriptionViewSet(CreateDestroyViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscribed_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, subscription=get_user(self)
        )


class AllSubscriptionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscribed_user


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return self.request.user.favorites_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, favorite=get_recipe(self)
        )


class ShoppingCartViewSet(CreateDestroyViewSet):
    serializer_class = ShoppingCartSerializer

    def get_queryset(self):
        return self.request.user.shopping_cart_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, shopping_cart=get_recipe(self)
        )
