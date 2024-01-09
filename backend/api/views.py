from djoser.serializers import SetPasswordSerializer
from rest_framework.mixins import ListModelMixin
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import (
    LimitOffsetPagination, PageNumberPagination
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ingredients.models import Ingredient
from recipes.models import Recipe
from tags.models import Tag
from users.models import User
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
from .supporting_functions import get_recipe, get_user


class MeViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDisplaySerializer
    http_method_names = ('get', 'head')
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        instance = request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ('get', 'head', 'post')
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDisplaySerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        else:
            return UserSignUpSerializer
    
    def get_permissions(self):
        if (self.action == 'set_password') or (self.action == 'me'):
            self.permission_classes = (IsAuthenticated,)
        else:
            self.permission_classes = (AllowAny,)
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(["post"], detail=False)
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        return Response(status=HTTP_204_NO_CONTENT)


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
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.subscribed_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, subscription=serializer.subscription
        )


class AllSubscriptionsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.subscribed_user


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.favorites_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, favorite=get_recipe(self)
        )


class ShoppingCartViewSet(CreateDestroyViewSet):
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.shopping_cart_user

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, shopping_cart=get_recipe(self)
        )
