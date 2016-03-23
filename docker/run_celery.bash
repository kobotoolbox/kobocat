#!/usr/bin/env bash
set -e

source /etc/profile

CELERYD_OPTIONS='--loglevel=DEBUG --time-limit=900 --maxtasksperchild=5'

cd "${KOBOCAT_SRC_DIR}"

exec /sbin/setuser wsgi python manage.py celeryd $CELERYD_OPTIONS
