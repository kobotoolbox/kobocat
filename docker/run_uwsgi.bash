#!/usr/bin/env bash
set -e

source /etc/profile


if [[ "$(stat -c '%U' ${KOBOCAT_LOGS_DIR})" != "${UWSGI_USER}" ]]; then
    echo 'Restoring ownership of Logs directory.'
    chown -R "${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"
fi

KOBOCAT_WEB_SERVER="${KOBOCAT_WEB_SERVER:-uWSGI}"
uwsgi_command="/sbin/setuser ${UWSGI_USER} /usr/local/bin/uwsgi --ini ${KOBOCAT_SRC_DIR}/docker/kobocat.ini"
if [[ "${KOBOCAT_WEB_SERVER,,}" == "uwsgi" ]]; then
    echo 'Running `kobocat` container with uWSGI application server.'
    exec ${uwsgi_command}
else
    echo 'Running `kobocat` container with `runserver_plus` debugging application server.'
    cd "${KOBOCAT_SRC_DIR}"
    pip install werkzeug ipython
    exec python manage.py runserver_plus 0:8000
fi
