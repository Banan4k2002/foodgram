import os

from django.core.wsgi import get_wsgi_application

from utils.shortlink_patch import shortlink_patch

shortlink_patch()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()
