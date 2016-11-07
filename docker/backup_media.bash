#!/usr/bin/env bash
set -e
source /etc/profile

KOBOCAT_MEDIA_URL="${KOBOCAT_MEDIA_URL:-media}"

timestamp="$(date +%Y.%m.%d.%H_%M)"
(cd "${KOBOCAT_SRC_DIR}" && tar cf "${BACKUPS_DIR}/kobocat_media__${timestamp}.tar" "${KOBOCAT_MEDIA_URL}")
