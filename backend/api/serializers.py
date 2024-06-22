from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import ValidationError
from shortlink.models import ShortLink

from api.fields import Base64ImageField
from api.pagination import RecipesLimitPagination
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

    def validate_tags(self, value):
        if len(value) == 0:
            raise ValidationError('Этот список не может быть пустым.')
        if len(value) != len(set(value)):
            raise ValidationError('Теги не должны повторяться.')
        return value

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise ValidationError('Этот список не может быть пустым.')
        ingredient_list = []
        for ingredient in value:
            ingredient_list.append(ingredient.get('id'))
        if len(ingredient_list) != len(set(ingredient_list)):
            raise ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate(self, data):
        if 'recipeingredients_set' in data:
            data['ingredients'] = data.get('recipeingredients_set')
        required_fields = (
            'ingredients',
            'tags',
            'name',
            'text',
            'cooking_time',
        )
        for field in required_fields:
            if field not in data:
                raise ValidationError({field: 'Обязательное поле'})
        data.pop('ingredients')

        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        serializer = RecipeGetSerializer(instance, context=context)
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredients_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)

        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient['id'].pk
            )
            RecipeIngredients.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount'],
            )

        request_path = self.context.get('request').get_full_path()
        short_link = ShortLink.objects.create(
            full_url=f'{request_path}{recipe.pk}'
        )
        recipe.short_link = short_link
        recipe.save()

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipeingredients_set')
        tags = validated_data.pop('tags')

        instance.name = validated_data.get('name')
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.save()

        instance.tags.set(tags)

        instance.recipeingredients_set.all().delete()
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient['id'].pk
            )
            RecipeIngredients.objects.create(
                ingredient=current_ingredient,
                recipe=instance,
                amount=ingredient['amount'],
            )
        return instance


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientsSerializer(
        many=True, source='recipeingredients_set'
    )
    tags = TagSerializer(many=True)
    author = UserGetSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(recipe=obj.pk, user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                recipe=obj.pk, user=user
            ).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('author', 'recipes', 'recipes_count')
        model = Subscription

    def get_recipes(self, obj):
        recipes = obj.author.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit:
            paginator = RecipesLimitPagination()
            paginated_recipes = paginator.paginate_queryset(
                queryset=recipes, request=request
            )
            serializer = ShortRecipeSerializer(paginated_recipes, many=True)
        else:
            serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data

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


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    recipe = ShortRecipeSerializer(read_only=True)

    class Meta:
        fields = ('recipe',)
        model = None

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
        if self.Meta.model.objects.filter(
            recipe=data['recipe'],
            user=data['user'],
        ).exists():
            raise ValidationError(
                {
                    'errors': f'Рецепт уже добавлен в {self.Meta.model._meta.verbose_name}'
                }
            )
        return data

    def create(self, validated_data):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('view').kwargs.get('pk')
        )
        user = self.context.get('request').user
        validated_data['recipe'] = recipe
        validated_data['user'] = user
        return self.Meta.model.objects.create(**validated_data)


class FavoriteSerializer(BaseUserRecipeSerializer):

    class Meta(BaseUserRecipeSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseUserRecipeSerializer):

    class Meta(BaseUserRecipeSerializer.Meta):
        model = ShoppingCart
