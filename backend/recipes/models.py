from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from shortlink.models import ShortLink

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название', max_length=32)
    slug = models.SlugField('Слаг', max_length=32, unique=True)


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единицы измерения', max_length=64)


class Recipe(models.Model):
    name = models.CharField('Название', max_length=256)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления', validators=(MinValueValidator(1),)
    )
    image = models.ImageField('Изображение', upload_to='recipes/images')
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredients'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    short_link = models.OneToOneField(
        ShortLink, on_delete=models.CASCADE, null=True
    )


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        'Количество', validators=(MinValueValidator(1),)
    )


class BaseUserRecipeModel(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='%(class)ss'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_%(class)s'
            ),
        )


class Favorite(BaseUserRecipeModel):
    pass


class ShoppingCart(BaseUserRecipeModel):
    pass
