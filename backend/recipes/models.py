from django.core.validators import MinValueValidator
from django.db import models

from ingredients.models import Ingredient
from tags.models import Tag
from users.models import User


class Recipe(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='название'
    )
    image = models.ImageField(verbose_name='картинка')
    text = models.TextField(verbose_name='текст')
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name='время приготовления'
    )
    is_favorited = models.BooleanField(
        default=False, verbose_name='в избранном'
    )
    is_in_shopping_cart = models.BooleanField(
        default=False, verbose_name='в корзине'
    )
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор'
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

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.SET_NULL, null=True
    )
    amount = models.IntegerField(default=1, validators=[MinValueValidator(1)])


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites_user'
    )
    favorite = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_favorite',
                fields=('user', 'favorite')
            ),
        )

    def __str__(self):
        return self.favorite


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart_user'
    )
    shopping_cart = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_recipes_in_shopping_cart',
                fields=('user', 'shopping_cart')
            ),
        )

    def __str__(self):
        return self.shopping_cart