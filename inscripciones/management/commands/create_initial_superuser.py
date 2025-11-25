# inscripciones/management/commands/create_initial_superuser.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Crea un superusuario inicial si aún no existe"

    def handle(self, *args, **options):
        User = get_user_model()

        # Si ya hay un superusuario, no hacemos nada
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Ya existe un superusuario. Nada que hacer."))
            return

        # Leemos credenciales desde variables de entorno (para Render)
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "Guillermo")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "9b9j3u5g")

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario '{username}' creado correctamente."
            )
        )
