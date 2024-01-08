from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_subscribed = models.BooleanField(
        default=False, editable=False, verbose_name='подписка'
    )

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

    def __str__(self):
        return self.subscription
