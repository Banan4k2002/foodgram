from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorPermission, PUTMethodPermission
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserGetSerializer,
    UserPostSerializer,
)
from recipes.models import Ingredient, Recipe, Tag
from users.models import Subscription

User = get_user_model()


class CreateReadViewSet(CreateModelMixin, ReadOnlyModelViewSet):
    pass


class UserViewSet(CreateReadViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = LimitPageNumberPagination

    @action(
        methods=('get',),
        detail=False,
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
    )
    def subscriptions(self, request):
        authors = Subscription.objects.filter(user=request.user)

        paginator = LimitPageNumberPagination()
        paginated_authors = paginator.paginate_queryset(
            queryset=authors, request=request
        )

        serializer = self.get_serializer(paginated_authors, many=True)
        return paginator.get_paginated_response(data=serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
    )
    def subscribe(self, request, pk):
        if request.method == 'DELETE':
            author = get_object_or_404(User, pk=pk)
            subscription = request.user.subscriptions.filter(author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Вы не подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=('get',),
        detail=False,
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data)

    @action(
        methods=('put', 'delete'),
        detail=False,
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=AvatarSerializer,
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data.get('avatar')
        user.save()
        return Response(
            data={'avatar': request.build_absolute_uri(user.avatar.url)}
        )

    @action(
        methods=('post',),
        detail=False,
        url_path='set_password',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=SetPasswordSerializer,
    )
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.data.get('new_password'))
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserPostSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.set_password(instance.password)
        instance.save()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    permission_classes = (PUTMethodPermission,)
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='favorite',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=FavoriteSerializer,
    )
    def favorite(self, request, pk):
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = request.user.favorites.filter(recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Данного рецепта нет в избранных'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=ShoppingCartSerializer,
    )
    def shopping_cart(self, request, pk):
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            cart = request.user.shoppingcarts.filter(recipe=recipe)
            if cart.exists():
                cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Данного рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(data={'short-link': recipe.short_link.short_url})

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return (IsAuthorPermission(),)
        elif self.action == 'create':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return super().get_serializer_class()
        elif self.action in ('create', 'partial_update'):
            return RecipePostSerializer
        else:
            return super().get_serializer_class()
