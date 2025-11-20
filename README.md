# LiFE - Sistema de inscripción (Django)

Proyecto base en Django para la Liga de Futbol Empresarial (LiFE).

## Requisitos

- Python 3.10+
- pip

## Cómo iniciar en local

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
# source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # para entrar a /admin
python manage.py runserver
```

1. Entra a `http://127.0.0.1:8000/admin` y crea al menos un **Torneo** marcando la casilla "Abierto".
2. Luego visita `http://127.0.0.1:8000/inscripcion/` para registrar equipos.

El proyecto usa SQLite por defecto para facilitar el arranque en local.
Posteriormente puedes cambiar la configuración de base de datos en `liga_life/settings.py` para usar PostgreSQL.
