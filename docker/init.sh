#!/bin/bash
set -e

echo 'Initializing KoBoCAT.'

oldpwd=$(pwd)
cd /srv/src/kobocat

echo 'Synchronizing database.'
python manage.py syncdb --noinput

# FIXME: Convince South that KPI has already done the overlapping migrations.
echo 'Running fake migrations.'
python manage.py migrate --noinput --fake oauth2_provider

echo 'Running migrations.'
python manage.py migrate --noinput


echo 'Completed initializing KoBoCAT.'

cd $oldpwd
