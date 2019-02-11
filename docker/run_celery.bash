#!/bin/bash
set -e
source /etc/profile

# Run the main Celery worker
cd "${KOBOCAT_SRC_DIR}"
exec /sbin/setuser "${UWSGI_USER}" celery worker -A onadata -Ofair --loglevel=info \
    --hostname=kobocat_main_worker@%h \
    --logfile=${KOBOCAT_LOGS_DIR}/celery.log \
    --pidfile=/tmp/celery.pid
