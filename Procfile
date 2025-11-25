web: python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_initial_superuser && gunicorn liga_life.wsgi:application --bind 0.0.0.0:$PORT
