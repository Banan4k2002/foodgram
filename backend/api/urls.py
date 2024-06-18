from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

v1_router = DefaultRouter()

v1_router.register(r'users', UserViewSet)
v1_router.register(r'tags', TagViewSet)
v1_router.register(r'ingredients', IngredientViewSet)
v1_router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
