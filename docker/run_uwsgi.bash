#!/usr/bin/env bash
set -e

source /etc/profile

exec /sbin/setuser wsgi /usr/local/bin/uwsgi --ini "${KOBOCAT_SRC_DIR}/docker/kobocat.ini"
