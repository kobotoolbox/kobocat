#!/bin/bash
set -e
source /etc/profile

# Run the main Celery worker
cd "${KOBOCAT_SRC_DIR}"
exec celery worker -A onadata --loglevel=debug \
    --hostname=main_worker@%h \
    --logfile=${KOBOCAT_LOGS_DIR}/celery.log \
    --pidfile=/tmp/celery.pid
