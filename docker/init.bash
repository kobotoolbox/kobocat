#!/bin/bash
set -e

source /etc/profile

echo 'KoBoCAT intializing...'

oldpwd=$(pwd)
cd "${KOBOCAT_SRC_DIR}"

echo 'Synchronizing database.'
python manage.py syncdb --noinput

echo 'Running migrations.'
python manage.py makemigrations
python manage.py migrate --noinput

rm -f /etc/cron.d/backup_media_crontab
if [[ -z "${KOBOCAT_MEDIA_BACKUP_SCHEDULE}" ]]; then
    echo 'KoBoCAT media automatic backups disabled.'
else
    # Should we first validate the schedule e.g. with `chkcrontab`?
    cat "${KOBOCAT_SRC_DIR}/docker/backup_media_crontab.envsubst" | envsubst > /etc/cron.d/backup_media_crontab
    echo "KoBoCAT media automatic backup schedule: ${KOBOCAT_MEDIA_BACKUP_SCHEDULE}"
fi

echo 'KoBoCAT initialization complete.'

cd $oldpwd
