from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from backend.constants import MAX_USERNAME_LENGTH


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        unique=True,
        verbose_name='адрес электронной почты'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),),
        verbose_name='имя пользователя'
    )
    first_name = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        verbose_name='имя'
    )
    last_name = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        verbose_name='фамилия'
    )

    class Meta:
        ordering = ('-date_joined',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_user',
        verbose_name='пользователь'
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='подписка'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_subscriptions',
                fields=('user', 'subscription')
            ),
            models.CheckConstraint(
                name='cannot_subscribe_to_self',
                check=~models.Q(user=models.F('subscription'))
            )
        )
        ordering = ('subscription',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return self.subscription
