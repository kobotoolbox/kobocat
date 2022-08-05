#!/usr/bin/env bash

source /etc/profile

if [[ "$(stat -c '%U' ${KOBOCAT_LOGS_DIR})" != "${UWSGI_USER}" ]]; then
    echo 'Restoring ownership of Logs directory.'
    chown -R "${UWSGI_USER}":"${UWSGI_GROUP}" "${KOBOCAT_LOGS_DIR}"
fi

KOBOCAT_WEB_SERVER="${KOBOCAT_WEB_SERVER:-uWSGI}"

cd "${KOBOCAT_SRC_DIR}"
if [[ "${KOBOCAT_WEB_SERVER,,}" == "uwsgi" ]]; then
    echo "Running \`KoBoCAT\` container with uWSGI application server."
    UWSGI_COMMAND="$(command -v uwsgi) --ini ${KOBOCAT_SRC_DIR}/docker/uwsgi.ini"
else
    echo "Running KoBoCAT container with \`runserver_plus\` debugging application server."
    UWSGI_COMMAND="gosu $UWSGI_USER python manage.py runserver_plus 0:8001"
fi
exec ${UWSGI_COMMAND}
