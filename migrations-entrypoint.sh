#!/bin/bash
set -e

echo "[Wait for mysql]"
./wait-for-it/wait-for-it.sh mysql:3306 --timeout=0

echo "[Wait for rabbitmq]"
./wait-for-it/wait-for-it.sh rabbitmq:5672 --timeout=0

echo "[Make migrations]"
python manage.py makemigrations --noinput

echo "[Clean old migrations]"
if [[ -d migrations ]]; then
  rm -rf migrations/*
fi

echo "[Copy migrations]"
for d in *
do
  if [[ -d $d/migrations ]]; then
    mkdir -p migrations/$d/migrations
    cp -r -f $d/migrations migrations/$d/.
  fi
done

echo "[Done]"
