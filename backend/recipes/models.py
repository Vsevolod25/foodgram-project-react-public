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
        verbose_name='название',
        verbose_name_plural='названия'
    )
    image = models.ImageField(
        upload_to='images/',
        verbose_name='картинка',
        verbose_name_plural='картинки'
    )
    text = models.TextField(
        verbose_name='текст', verbose_name_plural='тексты'
    )
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
        verbose_name='время приготовления',
        verbose_name_plural='время приготовления'
    )
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='пользователь',
        verbose_name_plural='пользователи'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='список ингредиентов',
        verbose_name_plural='списки ингредиентов'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='список тегов',
        verbose_name_plural='списки тегов'
    )

    class Meta:
        ordering = ('-pub_date', 'name',)

    def __str__(self):
        return self.name

    def favorited_num(self):
        return Favorite.objects.filter(favorite=self).count()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='рецепт',
        verbose_name_plural='рецепты'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='ингредиент',
        verbose_name_plural='ингредиенты'
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
        verbose_name='количество ингредиента',
        verbose_name_plural='количество ингредиентов'
    )

    class Meta:
        ordering = ('recipe',)

    def __str__(self):
        return self.recipe


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='рецепт',
        verbose_name_plural='рецепты'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='тег',
        verbose_name_plural='теги'
    )

    class Meta:
        ordering = ('recipe',)

    def __str__(self):
        return self.recipe


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites_user',
        verbose_name='пользователь',
        verbose_name_plural='пользователи'
    )
    favorite = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='избранный рецепт',
        verbose_name_plural='избранные рецепты'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_favorite',
                fields=('user', 'favorite')
            ),
        )
        ordering = ('favorite',)

    def __str__(self):
        return self.favorite


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user',
        verbose_name='пользователь',
        verbose_name_plural='пользователи'
    )
    shopping_cart = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='рецепт в корзине',
        verbose_name_plural='рецепты в корзине'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_shopping_cart',
                fields=('user', 'shopping_cart')
            ),
        )
        ordering = ('user',)

    def __str__(self):
        return self.shopping_cart
