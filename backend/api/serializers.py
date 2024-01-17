from base64 import b64decode

from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from ingredients.models import Ingredient
from recipes.models import (
    Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
)
from tags.models import Tag
from users.models import Subscription, User


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
        extra_kwargs = {field: {'required': True} for field in fields}

    def to_representation(self, instance):
        representation = super(
            UserCreateSerializer, self
        ).to_representation(instance)
        representation['id'] = instance.id

        return representation


class UserDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def to_representation(self, instance):
        representation = super(
            UserDisplaySerializer, self
        ).to_representation(instance)
        request = self.context['request']
        if request.user.is_authenticated:
            is_subscribed = Subscription.objects.filter(
                user=request.user, subscription=instance.id
            ).exists()
        else:
            is_subscribed = False
        representation['is_subscribed'] = is_subscribed

        return representation


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    subscription = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_subscription(self, obj):
        user_id = self.context['view'].kwargs['user_id']
        return get_object_or_404(User, id=user_id)
    
    def decode_image(self, image):
        image = str(image)
        if isinstance(image, str) and image.startswith('data:image'):
            format, imgstr = image.split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(b64decode(imgstr), name='image.' + ext)
        return image

    def to_representation(self, instance):
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        subscription_recipes = Recipe.objects.filter(
            author=instance.subscription
        )
        recipes_count = subscription_recipes.count()
        if recipes_limit is not None:
            subscription_recipes = subscription_recipes[:int(recipes_limit)]

        return {
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
                    'image': self.decode_image(current_recipe.image),
                    'cooking_time': current_recipe.cooking_time
                } for current_recipe in subscription_recipes
            ],
            'recipes_count': recipes_count
        }


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(required=True, write_only=True)
    author = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    ingredients = serializers.ListField(required=True, write_only=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_tags_for_recipe(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(
                recipe=recipe,
                tag=Tag.objects.get(id=tag)
            )

    def get_ingredients_for_recipe(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.get_tags_for_recipe(tags, recipe)
        self.get_ingredients_for_recipe(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().update(recipe, validated_data)
        RecipeTag.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.get_tags_for_recipe(tags, recipe)
        self.get_ingredients_for_recipe(ingredients, recipe)
        return recipe

    def validate(self, attrs):
        fields = (
            'tags', 'ingredients', 'name', 'image', 'text', 'cooking_time'
        )
        for field in fields:
            if field not in attrs:
                raise serializers.ValidationError(
                    f'Отсутствует обязательное поле - {field}.'
                )
        return super().validate(attrs)

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
                if key not in ingredient.keys():
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
            ingredient['amount'] = int(ingredient['amount'])
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1.'
                )
        return value

    def to_internal_value(self, data):
        try:
            image = data['image']
        except KeyError:
            return super().to_internal_value(data)
        if isinstance(image, str) and image.startswith('data:image'):
            format, imgstr = image.split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(b64decode(imgstr), name='image.' + ext)
            data['image'] = image

        return super().to_internal_value(data)

    def to_representation(self, instance):
        representation = super(
            RecipeSerializer, self
        ).to_representation(instance)
        request = self.context['request']
        if request.user.is_authenticated:
            is_favorited = Favorite.objects.filter(
                user=request.user, favorite=instance.id
            ).exists()
            is_in_shopping_cart = ShoppingCart.objects.filter(
                user=request.user, shopping_cart=instance.id
            ).exists()
        else:
            is_favorited = False
            is_in_shopping_cart = False
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
                'amount': RecipeIngredient.objects.get(
                    ingredient=ingredient, recipe=instance
                ).amount
            } for ingredient in instance.ingredients.all()
        ]
        representation['is_favorited'] = is_favorited
        representation['is_in_shopping_cart'] = is_in_shopping_cart
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    favorite = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = '__all__'

    def get_favorite(self, obj):
        recipe_id = self.context['view'].kwargs['recipe_id']
        return get_object_or_404(Recipe, id=recipe_id)

    def to_representation(self, instance):
        return {
            'id': instance.favorite.id,
            'name': instance.favorite.name,
            'image': str(instance.favorite.image),
            'cooking_time': instance.favorite.cooking_time
        }


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def get_shopping_cart(self, obj):
        recipe_id = self.context['view'].kwargs['recipe_id']
        return get_object_or_404(Recipe, id=recipe_id)

    def to_representation(self, instance):
        return {
            'id': instance.shopping_cart.id,
            'name': instance.shopping_cart.name,
            'image': str(instance.shopping_cart.image),
            'cooking_time': instance.shopping_cart.cooking_time
        }


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
