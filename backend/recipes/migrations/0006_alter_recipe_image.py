# Generated by Django 3.2.3 on 2024-01-11 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20240110_2213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(upload_to='media/', verbose_name='картинка'),
        ),
    ]
