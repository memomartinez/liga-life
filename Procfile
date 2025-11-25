web: python manage.py migrate --noinput && python manage.py create_initial_superuser && gunicorn liga_life.wsgi:application --bind 0.0.0.0:$PORT
