# Generated by Django 4.2.13 on 2024-06-22 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "recipes",
            "0005_alter_favorite_options_alter_ingredient_options_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="favorite",
            options={
                "verbose_name": "избранное",
                "verbose_name_plural": "Избранные",
            },
        ),
        migrations.AlterModelOptions(
            name="shoppingcart",
            options={
                "verbose_name": "корзину",
                "verbose_name_plural": "Корзины",
            },
        ),
    ]
