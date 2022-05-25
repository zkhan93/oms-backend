from django.conf import settings
from api.models import User
from django.core.management.base import BaseCommand
import logging


class Command(BaseCommand):
    def handle(self, *args, **options):
        username = settings.DJANGO_SUPERUSER_USERNAME
        password = settings.DJANGO_SUPERUSER_PASSWORD

        if not User.objects.filter(username=username).exists():
            logging.info(f"Creating account for {username}")
            User.objects.create_superuser(username=username, password=password)
        else:
            logging.info("Admin account has already been initialized.")
