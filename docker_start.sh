#!/bin/bash
set -e
export DJANGO_SETTINGS_MODULE=config.settings
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --timeout 300
