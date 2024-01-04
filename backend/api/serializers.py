from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.fields import CharField
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    subscription = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )

    class Meta:
        model = Subscription
        fields = '__all__'
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'subscription'),
                message='Нельзя несколько раз подписываться на одного автора.'
            ),
        )

    def validate_following(self, value):
        request = self.context['request']
        if value == request.user:
            raise serializers.ValidationError('Нельзя подписываться на себя.')
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    favorite = serializers.SlugRelatedField(
        slug_field='name', queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'favorite'),
                message='Рецепт уже находится в избранном.'
            ),
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    shopping_cart = serializers.SlugRelatedField(
        slug_field='name', queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'shopping_cart'),
                message='Рецепт уже находится в корзине.'
            ),
        )
