#web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT --timeout 300
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed_site_page_seo && gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT --timeout 300
