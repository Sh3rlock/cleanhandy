web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT --timeout 300
