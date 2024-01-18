from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from ingredients.models import Ingredient
from recipes.models import (
    Favorite, Recipe, RecipeIngredient, RecipeTag, ShoppingCart
)
from tags.models import Tag
from users.models import Subscription, User


class UserSignUpSerializer(UserCreateSerializer):
    email = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[
            RegexValidator(r'^[\w.@+-]+\z'),
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
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, subscription=obj.id
            ).exists()
        return False


class SubscribeSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    subscription = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'
    
    def get_subscription(self, obj):
        user_id = self.context['view'].kwargs['pk']
        return get_object_or_404(User, id=user_id)
    
    def validate(self, attrs):
        if self.subscription == self.user:
            raise ValidationError('Нельзя подписываться на себя.')
        if Subscription.objects.filter(
                user=self.user, subscription=self.subscription
            ).exists():
                raise ValidationError(
                    'Нельзя повторно подписываться на одного пользователя.'
                )
        return super().validate(attrs)
    
    def to_representation(self, instance):
        return SubscriptionsSerializer.to_representation(instance)


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
        if recipes_limit is not None:
            return Recipe.objects.filter(
                author=obj.subscription
            )[:int(recipes_limit)]
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
                    'image': current_recipe.image,
                    'cooking_time': current_recipe.cooking_time
                } for current_recipe in instance.recipes.all()
            ],
            'recipes_count': instance.recipes_count
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

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)
    
    def validate(self, attrs):
        for key in ('id', 'amount'):
            if key not in attrs.keys():
                raise serializers.ValidationError(
                    'Неверный формат ингредиентов.'
                )
        if not Ingredient.objects.filter(id=attrs['id']).exists():
            raise serializers.ValidationError(
                'Указанный ингредиент не найден.'
            )
        attrs['amount'] = int(attrs['amount'])
        if attrs['amount'] < 1:
            raise serializers.ValidationError(
                'Количество не может быть меньше 1.'
            )
        return super().validate(self, attrs)


class RecipeDisplayIngredientSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)
    
    def get_name(self, obj):
        return Ingredient.objects.get(id=obj.id).name
    
    def get_measurement_unit(self, obj):
        return Ingredient.objects.get(id=obj.id).measurement_unit

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'measurement_unit': instance.measurement_unit,
            'amount': instance.amount
        }


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = TagSerializer(required=True, many=True)
    author = UserDisplaySerializer(
        read_only=True, default=serializers.CurrentUserDefault()
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
        RecipeTag.objects.create(recipe=recipe, **tags)
        self.get_ingredients_for_recipe(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().update(recipe, validated_data)
        RecipeTag.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        RecipeTag.objects.create(recipe=recipe, **tags)
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
            if ingredient['id'] in ingredients:
                raise serializers.ValidationError(
                    'Нельзя добавлять один ингредиент дважды.'
                )
            ingredients.append(ingredient['id'])
        return value


class RecipeDisplaySerializer(serializers.ModelSerializer):
    tags = TagSerializer(required=True, many=True)
    author = UserDisplaySerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeDisplayIngredientSerializer(required=True, many=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        request = self.context['request']
        if request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, favorite=obj.id
            ).exists()
        return False
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, shopping_cart=obj.id
            ).exists()
        return False

    def to_representation(self, instance):
        representation = super(
            RecipeDisplaySerializer, self
        ).to_representation(instance)
        representation['tags'] = TagSerializer(many=True)
        representation['author'] = UserDisplaySerializer(
            many=True,
            fields=('email', 'id', 'username', 'first_name', 'last_name',)
        )
        return representation


class RecipeInCategoryDisplaySerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': str(instance.recipe.image),
            'cooking_time': instance.recipe.cooking_time
        }


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def get_recipe(self, obj):
        recipe_id = self.context['view'].kwargs['pk']
        return get_object_or_404(Recipe, id=recipe_id)
    
    def validate(self, attrs):
        if self.recipe is None:
            raise ValidationError('Указанного рецепта не существует.')
        if Favorite.objects.filter(
            user=self.user, favorite=self.recipe
        ).exists():
            raise ValidationError('Нельзя повторно добавлять рецепт в избранное.')
        return super().validate(attrs)
    
    def to_representation(self, instance):
        return RecipeInCategoryDisplaySerializer.to_representation(instance)


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def get_recipe(self, obj):
        recipe_id = self.context['view'].kwargs['pk']
        return Recipe.objects.get(id=recipe_id)
    
    def validate(self, attrs):
        if self.recipe is None:
            raise ValidationError('Указанного рецепта не существует.')
        if ShoppingCart.objects.filter(
            user=self.user, shopping_cart=self.recipe
        ).exists():
            raise ValidationError('Нельзя повторно добавлять рецепт в корзину.')
        return super().validate(attrs)

    def to_representation(self, instance):
        return RecipeInCategoryDisplaySerializer.to_representation(instance)
