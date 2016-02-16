#!/bin/bash
set -e

source /etc/profile

echo 'KoBoCAT intializing...'

oldpwd=$(pwd)
cd /srv/src/kobocat

echo 'Synchronizing database.'
python manage.py syncdb --noinput

# FIXME: Convince South that KPI has already done the overlapping migrations.
echo 'Running fake migrations.'
python manage.py migrate --noinput --fake oauth2_provider

echo 'Running migrations.'
python manage.py migrate --noinput


echo 'KoBoCAT initialization complete.'

cd $oldpwd
