"""
WSGI config for projectmanager project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanager.settings')

application = get_wsgi_application()
