#!/bin/bash
set -e
source /etc/profile

echo "Restoring permissions for \`backup\` and \`log\` folders..."
chown -R "${UWSGI_USER}":"${UWSGI_USER}" "${BACKUPS_DIR}"
chown -R "${UWSGI_USER}":"${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"
