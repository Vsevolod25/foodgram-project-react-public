# Generated by Django 3.2.3 on 2024-01-08 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_is_subscribed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_subscribed',
            field=models.BooleanField(default=False, editable=False, verbose_name='подписка'),
        ),
    ]
