#!/bin/bash
set -e
source /etc/profile

# Run the main Celery worker

cd "${KOBOCAT_SRC_DIR}"

AUTOSCALE_MIN="${CELERY_AUTOSCALE_MIN:-2}"
AUTOSCALE_MAX="${CELERY_AUTOSCALE_MAX:-6}"

exec celery -A onadata worker -Ofair --loglevel=info \
    --hostname=kobocat_main_worker@%h \
    --logfile=${KOBOCAT_LOGS_DIR}/celery.log \
    --pidfile=${CELERY_PID_DIR}/celery.pid \
    --uid=${UWSGI_USER} \
    --gid=${UWSGI_GROUP} \
    --autoscale ${AUTOSCALE_MIN},${AUTOSCALE_MAX}
