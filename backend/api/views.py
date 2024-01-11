from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User
from .functions import (
    add_recipe_to_category_validation,
    get_many_to_many_instance,
    get_many_to_many_list
)
from .mixins import CreateDestroyViewSet, ListRetrieveViewSet
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
    queryset = User.objects.all()
    http_method_names = ('get', 'head', 'post')
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDisplaySerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSignUpSerializer

    def get_permissions(self):
        if self.action in ('set_password', 'me'):
            self.permission_classes = (IsAuthenticated,)
        else:
            self.permission_classes = (AllowAny,)
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


class AllSubscriptionsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    http_method_names = ('get', 'head', 'post', 'patch', 'delete')
    order_by = ('pub_date', 'name',)
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        author = self.request.query_params.get('author')
        if author is not None:
            return queryset.filter(author=author)
        tag_slugs = self.request.GET.getlist('tags')
        if tag_slugs:
            tags = [Tag.objects.get(slug=slug).id for slug in tag_slugs]
            return queryset.filter(tags__in=tags)
        request = self.request
        if request.user.is_authenticated:
            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited is not None:
                return queryset.filter(
                    id__in=get_many_to_many_list(request, Favorite)
                )
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart'
            )
            if is_in_shopping_cart is not None:
                return queryset.filter(
                    id__in=get_many_to_many_list(request, ShoppingCart)
                )
        return queryset

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


class SubscriptionViewSet(CreateDestroyViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    http_method_names = ('head', 'post', 'delete')
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        user = self.request.user
        subscription = get_object_or_404(User, pk=self.kwargs.get('user_id'))
        if subscription == user:
            raise ValidationError('Нельзя подписываться на себя.')
        if Subscription.objects.filter(
            user=user, subscription=subscription
        ).exists():
            raise ValidationError(
                'Нельзя повторно подписываться на одного пользователя.'
            )
        serializer.save(user=user, subscription=subscription)

    @action(methods=['delete'], detail=False)
    def delete(self, request, user_id):
        instance = get_many_to_many_instance(request, user_id, Subscription)
        self.perform_destroy(instance)
        return Response(status=HTTP_204_NO_CONTENT)


class FavoriteViewSet(CreateDestroyViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        obj = add_recipe_to_category_validation(self, Favorite)
        serializer.save(user=self.request.user, favorite=obj)

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id):
        instance = get_many_to_many_instance(request, recipe_id, Favorite)
        self.perform_destroy(instance)
        return Response(status=HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(CreateDestroyViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        obj = add_recipe_to_category_validation(self, ShoppingCart)
        serializer.save(user=self.request.user, shopping_cart=obj)

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id):
        instance = get_many_to_many_instance(request, recipe_id, ShoppingCart)
        self.perform_destroy(instance)
        return Response(status=HTTP_204_NO_CONTENT)
