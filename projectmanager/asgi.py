"""
ASGI config for projectmanager project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanager.settings')

application = get_asgi_application()
