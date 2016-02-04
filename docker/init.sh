#!/bin/bash
set -e

oldpwd=$(pwd)
cd /srv/src/kobocat

# FIXME: Convince South that KPI has already done the overlapping migrations.
python manage.py migrate --fake oauth2_provider

python manage.py syncdb --noinput

python manage.py migrate --noinput

cd $oldpwd
