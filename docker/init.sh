#!/bin/bash
set -e

oldpwd=$(pwd)
cd /srv/src/kobocat

echo 'Waiting for Postgres.'
KOBO_PSQL_DB_NAME=${KOBO_PSQL_DB_NAME:-"kobotoolbox"}
KOBO_PSQL_DB_USER=${KOBO_PSQL_DB_USER:-"kobo"}
KOBO_PSQL_DB_PASS=${KOBO_PSQL_DB_PASS:-"kobo"}
dockerize -timeout=20s -wait ${PSQL_PORT}
until $(PGPASSWORD="${KOBO_PSQL_DB_PASS}" psql -d ${KOBO_PSQL_DB_NAME} -h psql -U ${KOBO_PSQL_DB_USER} -c '' 2> /dev/null); do
    sleep 1
done
echo 'Postgres ready.'

echo 'Synchronizing database.'
python manage.py syncdb --noinput

# FIXME: Convince South that KPI has already done the overlapping migrations.
echo 'Running fake migrations.'
python manage.py migrate --noinput --fake oauth2_provider

echo 'Running migrations.'
python manage.py migrate --noinput

echo '\`kobocat\` initialization completed.'

cd $oldpwd
