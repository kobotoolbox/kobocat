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

echo 'Running migrations...'
python manage.py migrate --noinput

rm -f /etc/cron.d/clean_up_tmp
cp docker/cron/clean_up_tmp /etc/cron.d/
echo 'KoBoCat tmp clean-up cron installed'

rm -f /etc/cron.d/backup_media_crontab
if [[ -z "${KOBOCAT_MEDIA_BACKUP_SCHEDULE}" ]]; then
    echo 'KoBoCAT media automatic backups disabled.'
else
    # Should we first validate the schedule e.g. with `chkcrontab`?
    cat "${KOBOCAT_SRC_DIR}/docker/backup_media_crontab.envsubst" | envsubst > /etc/cron.d/backup_media_crontab
    echo "KoBoCAT media automatic backup schedule: ${KOBOCAT_MEDIA_BACKUP_SCHEDULE}"
fi

/bin/bash ${KOBOCAT_SRC_DIR}/docker/sync_static.sh

# Keep it as is, not tested with Python3
rm -rf /etc/profile.d/pydev_debugger.bash.sh
if [[ -d /srv/pydev_orig && -n "${KOBOCAT_PATH_FROM_ECLIPSE_TO_PYTHON_PAIRS}" ]]; then
    echo 'Enabling PyDev remote debugging.'
    "${KOBOCAT_SRC_DIR}/docker/setup_pydev.bash"
fi

echo 'Cleaning up Celery PIDs...'
rm -rf /tmp/celery*.pid

echo 'KoBoCAT initialization complete.'

exec /usr/bin/runsvdir /etc/service
