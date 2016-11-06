#!/usr/bin/env bash
source /etc/profile

timestamp="$(date +%Y.%m.%d.%H_%M)"
(cd "${KOBOCAT_SRC_DIR}" && tar cf "${BACKUPS_DIR}/kobocat_media__${timestamp}.tar" media)
