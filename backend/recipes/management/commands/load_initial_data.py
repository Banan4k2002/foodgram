import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

MODELS_FILES = ((Ingredient, 'data/ingredients.json'), (Tag, 'data/tags.json'))


class Command(BaseCommand):
    help = 'Импорт данных из json файлов.'

    def handle(self, *args, **options):
        for model, json_file in MODELS_FILES:
            with open(json_file, 'r') as file:
                data = json.load(file)
                model.objects.all().delete()
                for item in data:
                    model.objects.create(**item)
