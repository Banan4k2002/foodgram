from django.contrib import admin
from django.urls import include, path

from api.views import get_recipe_by_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:shortlink>/', get_recipe_by_link),
]
