#!/bin/bash
set -e

rm -f /etc/cron.d/clean_up_tmp
cp docker/cron/clean_up_tmp /etc/cron.d/
echo 'KoBoCAT tmp clean-up cron installed'

rm -f /etc/cron.d/backup_media_crontab
if [[ -z "${KOBOCAT_MEDIA_BACKUP_SCHEDULE}" ]]; then
    echo 'KoBoCAT media automatic backups disabled.'
else
    # Should we first validate the schedule e.g. with `chkcrontab`?
    cat "${KOBOCAT_SRC_DIR}/docker/backup_media_crontab.envsubst" | envsubst > /etc/cron.d/backup_media_crontab
    echo "KoBoCAT media automatic backup schedule: ${KOBOCAT_MEDIA_BACKUP_SCHEDULE}"
fi
