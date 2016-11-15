#!/usr/bin/env bash
set -e
source /etc/profile

KOBOCAT_MEDIA_URL="${KOBOCAT_MEDIA_URL:-media}"

timestamp="$(date +%Y.%m.%d.%H_%M)"
backup_filename="kobocat_media__${timestamp}.tar"

(cd "${KOBOCAT_SRC_DIR}" && tar cf "${BACKUPS_DIR}/${backup_filename}" "${KOBOCAT_MEDIA_URL}")

echo "Backup file \`${backup_filename}\` created successfully."
