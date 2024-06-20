from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthorPermission(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class PUTMethodPermission(BasePermission):

    def has_permission(self, request, view):
        if request.method == 'PUT':
            raise MethodNotAllowed(request.method)
        return super().has_permission(request, view)
