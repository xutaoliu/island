#!/bin/bash

echo "[Wait for mysql]"
./wait-for-it/wait-for-it.sh mysql:3306 --timeout=0

echo "[Make migrations]"
python manage.py makemigrations --noinput

RESULT=$?
if [[ $RESULT -ne 0 ]]; then
    exit $RESULT
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
