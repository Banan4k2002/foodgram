from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscribers',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_subscription'
            ),
        )
