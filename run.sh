#! /bin/bash

python manage.py collectstatic
python manage.py migrate
python manage.py createcachetable
python manage.py initadmin

$@