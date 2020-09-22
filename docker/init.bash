#!/bin/bash
set -e

source /etc/profile

echo 'KoBoCAT intializing...'

cd "${KOBOCAT_SRC_DIR}"

if [[ -z $DATABASE_URL ]]; then
    echo "DATABASE_URL must be configured to run this server"
    echo "example: 'DATABASE_URL=postgres://hostname:5432/dbname'"
    exit 1
fi

# Wait for databases to be up & running before going further
/bin/bash "${INIT_PATH}/wait_for_mongo.bash"
/bin/bash "${INIT_PATH}/wait_for_postgres.bash"

echo 'Running migrations...'
python manage.py migrate --noinput

echo 'Setting up cron tasks...'
sudo -E ${KOBOCAT_SRC_DIR}/docker/setup_cron.bash
sudo -E ${KOBOCAT_SRC_DIR}/docker/setup_pydev_debugger.bash
sudo -E ${KOBOCAT_SRC_DIR}/docker/sync_static.bash

echo 'Cleaning up Celery PIDs...'
rm -rf ${CELERY_PID_DIR}/*.pid

echo 'KoBoCAT initialization complete.'

exec /usr/bin/runsvdir "${SERVICES_DIR}"
