from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


class UserRecipeMixin:

    def base_user_recipe_action(
        self, request, pk, instance_model, error_message
    ):
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            instance = instance_model.objects.filter(
                user=request.user, recipe=recipe
            )
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
