#! /bin/bash

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createcachetable
python manage.py initadmin

$@