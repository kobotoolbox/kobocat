#!/usr/bin/env bash
set -e

source /etc/profile


if [[ "$(stat -c '%U' ${KOBOCAT_LOGS_DIR})" != "${UWSGI_USER}" ]]; then
    echo 'Restoring ownership of Logs directory.'
    chown -R "${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"
fi

exec /sbin/setuser "${UWSGI_USER}" /usr/local/bin/uwsgi --ini "${KOBOCAT_SRC_DIR}/docker/kobocat.ini"
