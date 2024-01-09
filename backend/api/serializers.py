from django.shortcuts import get_object_or_404
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
from tags.models import Tag
from users.models import Subscription, User
from .supporting_functions import (
    favorite_check, shopping_cart_check, subscription_check
)


class UserSignUpSerializer(UserCreateSerializer):
    email = serializers.CharField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(r'^[\w.@+-]+$'),
            UniqueValidator(queryset=User.objects.all())
        ]
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password',)
        extra_kwargs = {field:{'required': True} for field in fields}

    def to_representation(self, instance):
        representation = super(
            UserCreateSerializer, self
        ).to_representation(instance)
        representation['id'] = instance.id

        return representation


class UserDisplaySerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        pk = request.parser_context.get('kwargs').get('pk')
        user_id = request.user.id
        return subscription_check(user_id, pk)


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
    subscription = serializers.SerializerMethodField()

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
    
    def get_subscription(self, obj):
        return get_object_or_404(User, pk=self.kwargs.get('user_id'))

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
    tags = serializers.ListField(required=True, write_only=True)
    author = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    ingredients = serializers.ListField(required=True, write_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'
    
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTag.objects.create(
                recipe=recipe,
                tag=Tag.objects.get(id=tag)
            )
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for tag in tags:
            RecipeTag.objects.create(
                recipe=instance,
                tag=Tag.objects.get(id=tag)
            )
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
        return instance
    
    def validate(self, attrs):
        fields = ('tags', 'ingredients', 'name', 'image', 'text', 'cooking_time',)
        for field in fields:
            if field not in attrs:
                raise serializers.ValidationError(
                    'Отсутствует обязательное поле.'
                )
        return super().validate(attrs)

    def get_is_favorited(self, obj):
        return False
    
    def get_is_in_shopping_cart(self, obj):
        return False

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                    'Необходимо указать теги.'
                )
        tags = []
        for tag in value:
            if tag in tags:
                raise serializers.ValidationError(
                    'Нельзя добавлять один тег дважды.'
                )
            tags.append(tag)
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError('Указанный тег не найден.')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                    'Необходимо указать ингредиенты.'
                )
        ingredients = []
        for ingredient in value:
            for key in ('id', 'amount'):
                if not key in ingredient.keys():
                    raise serializers.ValidationError(
                        'Неверный формат ингредиентов.'
                    )
            if ingredient['id'] in ingredients:
                raise serializers.ValidationError(
                    'Нельзя добавлять один ингредиент дважды.'
                )
            ingredients.append(ingredient['id'])
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    'Указанный ингредиент не найден.'
                )
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1.'
                )
        return value

    def to_representation(self, instance):
        representation = super(
            RecipeSerializer, self
        ).to_representation(instance)
        representation['tags'] = [
            {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'slug': tag.slug
            } for tag in instance.tags.all()
        ]
        representation['author'] = {
            'id': instance.author.id,
            'username': instance.author.username,
            'first_name': instance.author.first_name,
            'last_name': instance.author.last_name,
            'email': instance.author.email
        }
        representation['ingredients'] = [
            {
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': RecipeIngredient.objects.get(ingredient=ingredient, recipe=instance).amount
            } for ingredient in instance.ingredients.all()
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
