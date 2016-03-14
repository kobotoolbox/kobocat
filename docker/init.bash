#!/bin/bash
set -e

source /etc/profile

echo 'KoBoCAT intializing...'

oldpwd=$(pwd)
cd /srv/src/kobocat

echo 'Synchronizing database.'
python manage.py syncdb --noinput

echo 'Running migrations.'
python manage.py makemigrations
python manage.py migrate --noinput


echo 'KoBoCAT initialization complete.'

cd $oldpwd
