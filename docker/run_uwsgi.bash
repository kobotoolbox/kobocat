#!/usr/bin/env bash
set -e

source /etc/profile


if [[ "$(stat -c '%U' ${KOBOCAT_LOGS_DIR})" != "${UWSGI_USER}" ]]; then
    echo 'Restoring ownership of Logs directory.'
    chown -R "${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"
fi

KOBOCAT_WEB_SERVER="${KOBOCAT_WEB_SERVER:-uWSGI}"
uwsgi_command="/sbin/setuser ${UWSGI_USER} $(command -v uwsgi) --ini ${KOBOCAT_SRC_DIR}/docker/kobocat.ini"

if [[ "${KOBOCAT_WEB_SERVER,,}" == "uwsgi" ]]; then
    cd "${KOBOCAT_SRC_DIR}"
    DIFF=$(diff "${KOBOCAT_SRC_DIR}/dependencies/pip/prod.txt" "/srv/tmp/pip_dependencies.txt")
    if [[ -n "$DIFF" ]]; then
        echo "Syncing pip dependencies..."
        pip-sync dependencies/pip/prod.txt 1>/dev/null
        cp "dependencies/pip/prod.txt" "/srv/tmp/pip_dependencies.txt"
    fi
    echo 'Running `kobocat` container with uWSGI application server.'
    exec ${uwsgi_command}
else
    cd "${KOBOCAT_SRC_DIR}"
    DIFF=$(diff "${KOBOCAT_SRC_DIR}/dependencies/pip/dev.txt" "/srv/tmp/pip_dependencies.txt")
    if [[ -n "$DIFF" ]]; then
        echo "Syncing pip dependencies..."
        pip-sync dependencies/pip/dev.txt 1>/dev/null
        cp "dependencies/pip/dev.txt" "/srv/tmp/pip_dependencies.txt"
    fi

    if [[ -n "$RAVEN_DSN" ]]; then
        echo "Sentry detected. Installing \`raven\` pip dependency..."
        pip install raven
    fi

    echo 'Running `kobocat` container with `runserver_plus` debugging application server.'
    exec python manage.py runserver_plus 0:8001
fi
