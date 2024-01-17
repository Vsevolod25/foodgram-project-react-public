from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.viewsets import ModelViewSet

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User
from .functions import (
    add_recipe_to_category_validation,
    get_many_to_many_instance,
    get_many_to_many_list
)
from .mixins import ListRetrieveViewSet
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    FavoriteSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserDisplaySerializer,
    UserSignUpSerializer
)


class UsersViewSet(ModelViewSet):
    http_method_names = ('get', 'head', 'post', 'delete')
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if self.action == 'subscribe':
            return Subscription.objects.all()
        if self.action == 'subscriptions':
            return Subscription.objects.filter(user=self.request.user)
        return User.objects.all()

    def get_serializer_class(self):
        if self.action in ('subscribe', 'subscriptions'):
            return SubscriptionSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.request.method == 'POST':
            return UserSignUpSerializer
        return UserDisplaySerializer

    def get_permissions(self):
        if self.action in (
            'set_password', 'me', 'subscribe', 'subscriptions'
        ):
            self.permission_classes = (IsAuthenticated,)
        elif self.request.method in ('GET', 'POST'):
            self.permission_classes = (AllowAny,)
        else:
            self.permission_classes = (IsAdminUser,)
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['post'], detail=False)
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, pk):
        if self.request.method == 'POST':
            user = self.request.user
            subscription = get_object_or_404(User, pk=pk)
            if subscription == user:
                raise ValidationError('Нельзя подписываться на себя.')
            if Subscription.objects.filter(
                user=user, subscription=subscription
            ).exists():
                raise ValidationError(
                    'Нельзя повторно подписываться на одного пользователя.'
                )
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, subscription=subscription)
            return Response(serializer.data, status=HTTP_201_CREATED)
        instance = get_many_to_many_instance(request, pk, Subscription)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RecipeViewSet(ModelViewSet):
    http_method_names = ('get', 'head', 'post', 'patch', 'delete')
    order_by = ('-pub_date', 'name')
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if self.action == 'favorite':
            return Favorite.objects.all()
        if self.action in ('shopping_cart', 'download_shopping_cart'):
            return ShoppingCart.objects.all()
        queryset = Recipe.objects.all()
        request = self.request
        if request.user.is_authenticated:
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart'
            )
            if is_in_shopping_cart is not None:
                return queryset.filter(
                    id__in=get_many_to_many_list(request, ShoppingCart)
                )
            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited is not None:
                queryset = queryset.filter(
                    id__in=get_many_to_many_list(request, Favorite)
                )
        author = self.request.query_params.get('author')
        if author is not None:
            queryset = queryset.filter(author=author)
        tag_slugs = self.request.GET.getlist('tags')
        if tag_slugs:
            tags = [Tag.objects.get(slug=slug).id for slug in tag_slugs]
            queryset = queryset.filter(tags__in=tags).distinct()
        return queryset

    def get_serializer_class(self):
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.action in ('shopping_cart', 'download_shopping_cart'):
            return ShoppingCartSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in (
            'favorite', 'shopping_cart', 'download_shopping_cart'
        ):
            self.permission_classes = (IsAuthenticated,)
        else:
            self.permission_classes = (IsAuthorOrReadOnly,)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(
            tags=self.request.data['tags'],
            ingredients=self.request.data['ingredients']
        )

    def perform_update(self, serializer):
        serializer.save(
            tags=self.request.data['tags'],
            ingredients=self.request.data['ingredients']
        )

    def create_shopping_cart_txt(self, request):
        shopping_cart_recipes = [
            Recipe.objects.get(id=id) for id in get_many_to_many_list(
                request, ShoppingCart
            )
        ]

        ingredients = {}
        for recipe in shopping_cart_recipes:
            for ingredient in recipe.ingredients.all():
                amount = RecipeIngredient.objects.get(
                    recipe=recipe, ingredient=ingredient
                ).amount
                name_unit = f'{ingredient.name},{ingredient.measurement_unit}'
                if name_unit not in ingredients.keys():
                    ingredients[name_unit] = amount
                else:
                    ingredients[name_unit] += amount

        with open(
            f'static/shopping_carts/{request.user}_shopping_cart.txt', 'w'
        ) as f:
            f.write('Список ингредиентов: \n')
            for ingredient in ingredients.keys():
                name_unit = ingredient.split(',')
                row = (
                    f'{name_unit[0]}: {ingredients[ingredient]} '
                    f'{name_unit[1]} \n'
                )
                f.write(row)
        return f'static/shopping_carts/{request.user}_shopping_cart.txt'

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        if self.request.method == 'POST':
            obj = add_recipe_to_category_validation(self, Favorite)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user, favorite=obj)
            return Response(serializer.data, status=HTTP_201_CREATED)
        instance = get_many_to_many_instance(request, pk, Favorite)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        if self.request.method == 'POST':
            obj = add_recipe_to_category_validation(self, ShoppingCart)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user, shopping_cart=obj)
            return Response(serializer.data, status=HTTP_201_CREATED)
        instance = get_many_to_many_instance(request, pk, ShoppingCart)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(['get'], detail=False)
    def download_shopping_cart(self, request):
        shopping_cart = self.create_shopping_cart_txt(request)
        return FileResponse(open(shopping_cart, 'rb'))


class IngredientViewSet(ListRetrieveViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name is not None:
            return queryset.filter(name__istartswith=name)
        return queryset


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
