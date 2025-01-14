# Generated by Django 3.2.3 on 2024-01-12 17:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='favorite',
            name='favorite',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='favorites',
                to='recipes.recipe',
                verbose_name='избранный рецепт'
            ),
        ),
        migrations.AlterField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='favorites_user',
                to=settings.AUTH_USER_MODEL,
                verbose_name='пользователь'
            ),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(
                upload_to='images/', verbose_name='картинка'
            ),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='recipe',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='recipes.recipe'
            ),
        ),
        migrations.AlterField(
            model_name='recipetag',
            name='recipe',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='recipes.recipe'
            ),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='shopping_cart',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_cart',
                to='recipes.recipe',
                verbose_name='рецепт в корзине'
            ),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_cart_user',
                to=settings.AUTH_USER_MODEL,
                verbose_name='пользователь'
            ),
        ),
    ]
