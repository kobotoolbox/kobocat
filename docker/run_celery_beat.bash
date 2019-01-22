#!/bin/bash
set -e
source /etc/profile

# Run the main Celery beat worker
cd "${KOBOCAT_SRC_DIR}"
exec celery beat -A onadata --loglevel=debug \
    --logfile=${KOBOCAT_LOGS_DIR}/celery_beat.log \
    --pidfile=/tmp/celery_beat.pid \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
