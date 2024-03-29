#!/bin/bash
set -e

echo "[Collect static files]"
python manage.py collectstatic --noinput

echo "[Wait for mysql]"
./wait-for-it/wait-for-it.sh mysql:3306 --timeout=0

echo "[Wait for redis]"
./wait-for-it/wait-for-it.sh redis:6379 --timeout=0

echo "[Wait for rabbitmq]"
./wait-for-it/wait-for-it.sh rabbitmq:5672 --timeout=0

echo "[Apply database migrations]"
python manage.py migrate --noinput

echo "[Start celery worker]"
celery worker -A island --detach -l info --logfile=log/celery.log --pidfile=celery.pid

echo "[Start celery beat]"
celery beat -A island --detach -S django -l info --logfile=log/celerybeat.log --pidfile=celerybeat.pid

echo "[Starting server]"
gunicorn --worker-class=gevent --workers=$GUNICORN_WORKERS --bind=0.0.0.0:8000 island.wsgi
