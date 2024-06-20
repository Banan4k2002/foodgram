from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6


class RecipesLimitPagination(PageNumberPagination):
    page_size_query_param = 'recipes_limit'
    page_query_param = None
