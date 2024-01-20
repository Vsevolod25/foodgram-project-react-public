from django.core.validators import MaxValueValidator, MinValueValidator
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.constants import (
    MAX_INGREDIENT_AMOUNT,
    MIN_INGREDIENT_AMOUNT
)
from ingredients.models import Ingredient
from recipes.models import (
    Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
)
from tags.models import Tag
from users.models import Subscription, User


class UserSignUpSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )


class UserDisplaySerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user, subscription=obj.id
            ).exists()
        )


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'subscription',)

    def validate(self, attrs):
        user = attrs['user']
        subscription = attrs['subscription']
        if user == subscription:
            raise ValidationError('Нельзя подписываться на себя.')
        if Subscription.objects.filter(
            user=user, subscription=subscription
        ).exists():
            raise ValidationError(
                'Нельзя повторно подписываться на одного пользователя.'
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        return SubscriptionsSerializer.to_representation(self, instance)


class SubscriptionsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                return Recipe.objects.filter(
                    author=obj.subscription
                )[:int(recipes_limit)]
            except ValueError:
                pass
        return Recipe.objects.filter(author=obj.subscription)

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.subscription).count()

    def to_representation(self, instance):
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
                    'image': str(current_recipe.image),
                    'cooking_time': current_recipe.cooking_time
                } for current_recipe in SubscriptionsSerializer.get_recipes(
                    self, instance
                ).all()
            ],
            'recipes_count': SubscriptionsSerializer.get_recipes_count(
                self, instance
            )
        }


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=(
                    'Объем ингредиента не может быть '
                    f'меньше {MIN_INGREDIENT_AMOUNT}.'
                )
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message=(
                    'Объем ингредиента не может быть '
                    f'больше {MAX_INGREDIENT_AMOUNT}.'
                )
            )
        ],
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeDisplayIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeDisplaySerializer(serializers.ModelSerializer):
    tags = TagSerializer(required=True, many=True)
    author = UserDisplaySerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeDisplayIngredientSerializer(
        required=True, many=True, source='recipe_ingredient'
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        request = self.context.get('request', None)
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, recipe=obj.id
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', None)
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj.id
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), required=True, many=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeCreateIngredientSerializer(required=True, many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_tags_for_recipe(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(
                recipe=recipe,
                tag=tag
            )

    def get_ingredients_for_recipe(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
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

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить картинку.'
            )
        return value

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
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты.'
            )
        ingredients = []
        for ingredient in value:
            if ingredient['id'] in ingredients:
                raise serializers.ValidationError(
                    'Нельзя добавлять один ингредиент дважды.'
                )
            ingredients.append(ingredient['id'])
        return value

    def to_representation(self, instance):
        return RecipeDisplaySerializer().to_representation(instance)


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']
        if recipe is None:
            raise ValidationError('Указанного рецепта не существует.')
        if Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            raise ValidationError(
                'Нельзя повторно добавлять рецепт в избранное.'
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': str(instance.recipe.image),
            'cooking_time': instance.recipe.cooking_time
        }


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']
        if recipe is None:
            raise ValidationError('Указанного рецепта не существует.')
        if ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            raise ValidationError(
                'Нельзя повторно добавлять рецепт в корзину.'
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': str(instance.recipe.image),
            'cooking_time': instance.recipe.cooking_time
        }
