from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User
from .supporting_functions import (
    favorite_check, shopping_cart_check, subscription_check
)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
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

    def validate_subscription(self, value):
        request = self.context['request']
        if value == request.user:
            raise serializers.ValidationError('Нельзя подписываться на себя.')
        return value
    
    def to_representation(self, instance):
        subscription_recipes = Recipe.objects.filter(author=instance.subscription)
        representation = {
            'email': instance.subscription.email,
            'id': instance.subscription.id,
            'username': instance.subscription.username,
            'first_name': instance.subscription.first_name,
            'last_name': instance.subscription.last_name,
            'is_subscribed': True,
            'recipes': [
                {
                    'id': current_recipe.id,
                    'name': current_recipe.name,
                    'image': current_recipe.image,
                    'cooking_time': current_recipe.cooking_time
                } for current_recipe in subscription_recipes
            ],
            'recipe_count': subscription_recipes.count()
        }

        return representation


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.MultipleChoiceField(
        choices=Tag.objects.all(), required=True
    )
    author = SlugRelatedField(slug_field='username', read_only=True)
    ingredients = serializers.MultipleChoiceField(
        choices=Ingredient.objects.all(), required=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        return favorite_check(self.author, self.instance)
    
    def get_in_shopping_cart(self, obj):
        return shopping_cart_check(self.author, self.instance)

    def to_representation(self, instance):
        representation = super(
            RecipeSerializer, self
        ).to_representation(instance)
        representation['tags'] = [
            {
                'id': current_tag.id,
                'name': current_tag.name,
                'color': current_tag.color,
                'slug': current_tag.slug
            } for current_tag in instance.tags.all()
        ]
        representation['author'] = {
            'email': instance.author.email,
            'id': instance.author.id,
            'username': instance.author.username,
            'first_name': instance.author.first_name,
            'last_name': instance.author.last_name,
            'is_subscribed': subscription_check(self.author, instance.author)
        }
        representation['ingredients'] = [
            {
                'id': current_ingredient.id,
                'name': current_ingredient.name,
                'measurement_unit': current_ingredient.measurement_unit,
                'amount': RecipeIngredient.objects.get(
                    recipe=instance, ingredient=current_ingredient
                ).amount
            } for current_ingredient in instance.ingredients.all()
        ]

        return representation


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
