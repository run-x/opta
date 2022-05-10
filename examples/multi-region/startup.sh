#!/bin/bash

export PYTHONPATH=$(pwd)

if [[ -z $DJANGO_SUPERUSER_PASSWORD ]]; then export DJANGO_SUPERUSER_PASSWORD=admin; fi

echo "Starting Django server..."
echo "Running Create Super User command..."
python manage.py createsuperuser --username admin --email admin@runx.dev --noinput --skip-checks
echo "Running Make Migrations command..."
python manage.py makemigrations
echo "Running Migrate command..."
python manage.py migrate
echo "Running Collect Static command..."
python manage.py collectstatic --noinput
echo "Running Start Server command..."
python manage.py runserver 0.0.0.0:8000
