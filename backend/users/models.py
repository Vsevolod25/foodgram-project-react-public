from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from backend.constants import MAX_USERNAME_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='адрес электронной почты',
        verbose_name_plural='адреса электронной почты'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=(
            RegexValidator(
                r'^[\w.@+-]+\z',
                message='Имя пользователя содержит неразрешенные символы.'
            ),
        ),
        verbose_name='имя пользователя',
        verbose_name_plural='имена пользователей'
    )
    first_name = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        verbose_name='имя',
        verbose_name_plural='имена'
    )
    last_name = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        verbose_name='фамилия',
        verbose_name_plural='фамилии'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'username', 'first_name', 'last_name']

    class Meta:
        ordering = ('-date_joined')

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_user',
        verbose_name='пользователь',
        verbose_name_plural='пользователи'
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='подписка',
        verbose_name_plural='подписки'
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
        ordering = ('subscription')

    def __str__(self):
        return self.subscription
