#!/usr/bin/env bash
set -e

source /etc/profile

CELERYD_OPTIONS="-Ofair --beat --loglevel=DEBUG"

cd "${KOBOCAT_SRC_DIR}"

exec /sbin/setuser wsgi python manage.py celeryd $CELERYD_OPTIONS
