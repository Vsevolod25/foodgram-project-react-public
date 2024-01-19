from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from backend.constants import (
    MAX_COOKING_TIME,
    MAX_FIELD_LENGTH,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)
from ingredients.models import Ingredient
from tags.models import Tag
from users.models import User


class Recipe(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='название'
    )
    image = models.ImageField(upload_to='images/', verbose_name='картинка')
    text = models.TextField(verbose_name='описание')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message='Время приготовления не может быть меньше 1.'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message='Время приготовления не может быть больше 32000.'
            )
        ],
        verbose_name='время приготовления'
    )
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='пользователь'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='теги'
    )

    class Meta:
        ordering = ('-pub_date', 'name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def favorited_num(self):
        return Favorite.objects.filter(favorite=self).count()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message='Объем ингредиента не может быть меньше 1.'
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message='Объем ингредиента не может быть больше 32000.'
            )
        ],
        verbose_name='количество ингредиента'
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return self.recipe


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='тег'
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'

    def __str__(self):
        return self.recipe


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites_user',
        verbose_name='пользователь'
    )
    favorite = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='избранный рецепт'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_favorite',
                fields=('user', 'favorite')
            ),
        )
        ordering = ('favorite',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return self.favorite


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user',
        verbose_name='пользователь'
    )
    shopping_cart = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='рецепт в корзине'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_shopping_cart',
                fields=('user', 'shopping_cart')
            ),
        )
        ordering = ('user',)
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзинах'

    def __str__(self):
        return self.shopping_cart
