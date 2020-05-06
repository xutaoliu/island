#!/bin/bash

echo "[Collect static files]"
python manage.py collectstatic --noinput

echo "[Apply database migrations]"
python manage.py migrate --noinput

echo "[Start celery worker]"
celery multi start island -A island -l info --logfile=log/celery.log --pidfile=celery.pid

echo "[Starting server]"
python manage.py runserver 0.0.0.0:8000 --noreload
