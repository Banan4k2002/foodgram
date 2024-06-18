import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Subscription.objects.filter(
                author=obj.pk, user=user
            ).exists()
        return False


class UserPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
        }

    def validate_password(self, value):
        validate_password(value)
        return value


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientsPostSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = RecipeIngredients
        fields = (
            'ingredient',
            'amount',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredient_representation = representation.pop('ingredient')
        return ingredient_representation | representation


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientsPostSerializer(
        many=True, source='recipeingredients_set'
    )
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def create(self, validated_data):
        print(validated_data)
        ingredients = validated_data.pop('recipeingredients_set')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient['id']
            )
            RecipeIngredients.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount'],
            )
        return recipe


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientsSerializer(
        many=True, source='recipeingredients_set'
    )
    tags = TagSerializer(many=True)
    author = UserGetSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    recipes = ShortRecipeSerializer(
        many=True, read_only=True, source='author.recipes'
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('author', 'recipes', 'recipes_count')
        model = Subscription

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        author_representation = representation.pop('author')
        avatar = author_representation.pop('avatar')
        representation['avatar'] = avatar
        return author_representation | representation

    def validate(self, data):
        author = get_object_or_404(
            User, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        if author == user:
            raise ValidationError(
                {'errors': 'Нельзя подписываться на самого себя'}
            )
        data['author'] = author
        data['user'] = user
        if Subscription.objects.filter(
            author=data['author'],
            user=data['user'],
        ).exists():
            raise ValidationError(
                {'errors': 'Вы уже подписаны на данного пользователя'}
            )
        return data

    def create(self, validated_data):
        author = get_object_or_404(
            User, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        validated_data['author'] = author
        validated_data['user'] = user
        return Subscription.objects.create(**validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = ShortRecipeSerializer(read_only=True)

    class Meta:
        fields = ('recipe',)
        model = Favorite

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation.pop('recipe')

    def validate(self, data):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        data['recipe'] = recipe
        data['user'] = user
        if Favorite.objects.filter(
            recipe=data['recipe'],
            user=data['user'],
        ).exists():
            raise ValidationError(
                {'errors': 'Рецепт уже добавлен в избранное'}
            )
        return data

    def create(self, validated_data):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        validated_data['recipe'] = recipe
        validated_data['user'] = user
        return Favorite.objects.create(**validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = ShortRecipeSerializer(read_only=True)

    class Meta:
        fields = ('recipe',)
        model = ShoppingCart

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation.pop('recipe')

    def validate(self, data):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        data['recipe'] = recipe
        data['user'] = user
        if ShoppingCart.objects.filter(
            recipe=data['recipe'],
            user=data['user'],
        ).exists():
            raise ValidationError({'errors': 'Рецепт уже добавлен в корзину'})
        return data

    def create(self, validated_data):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        validated_data['recipe'] = recipe
        validated_data['user'] = user
        return ShoppingCart.objects.create(**validated_data)
