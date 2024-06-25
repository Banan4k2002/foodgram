from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet, NumberFilter)

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = CharFilter(method='get_tags')
    is_in_shopping_cart = BooleanFilter(method='get_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='get_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shoppingcarts__user=user)
        return queryset

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_tags(self, queryset, name, value):
        tag_slugs = self.request.query_params.getlist('tags')
        print(tag_slugs)
        return queryset.filter(tags__slug__in=tag_slugs).distinct()
