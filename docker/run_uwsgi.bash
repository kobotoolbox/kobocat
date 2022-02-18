#!/usr/bin/env bash

source /etc/profile

if [[ "$(stat -c '%U' ${KOBOCAT_LOGS_DIR})" != "${UWSGI_USER}" ]]; then
    echo 'Restoring ownership of Logs directory.'
    chown -R "${UWSGI_USER}":"${UWSGI_GROUP}" "${KOBOCAT_LOGS_DIR}"
fi

KOBOCAT_WEB_SERVER="${KOBOCAT_WEB_SERVER:-uWSGI}"

if [[ "${KOBOCAT_WEB_SERVER,,}" == "uwsgi" ]]; then
    cd "${KOBOCAT_SRC_DIR}"
    DIFF=$(diff "${KOBOCAT_SRC_DIR}/dependencies/pip/prod.txt" "${TMP_DIR}/pip_dependencies.txt")
    if [[ -n "$DIFF" ]]; then
        # Celery services need to be stopped to avoid raising errors
        # during pip-sync
        echo "Stopping Celery services..."
        sv stop celery
        sv stop celery_beat
        echo "Syncing pip dependencies..."
        pip-sync dependencies/pip/prod.txt 1>/dev/null
        cp "dependencies/pip/prod.txt" "${TMP_DIR}/pip_dependencies.txt"
        echo "Restarting Celery..."
        sv start celery
        sv start celery_beat
    fi
    echo "Running \`KoBoCAT\` container with uWSGI application server."
    UWSGI_COMMAND="$(command -v uwsgi) --ini ${KOBOCAT_SRC_DIR}/docker/kobocat.ini"
else
    cd "${KOBOCAT_SRC_DIR}"
    DIFF=$(diff "${KOBOCAT_SRC_DIR}/dependencies/pip/dev.txt" "${TMP_DIR}/pip_dependencies.txt")
    if [[ -n "$DIFF" ]]; then
        # Celery services need to be stopped to avoid raising errors during
        # pip-sync
        echo "Stopping Celery services..."
        sv stop celery
        sv stop celery_beat
        echo "Syncing pip dependencies..."
        gosu "${UWSGI_USER}" pip-sync dependencies/pip/dev.txt 1>/dev/null
        cp "dependencies/pip/dev.txt" "${TMP_DIR}/pip_dependencies.txt"
        echo "Restarting Celery..."
        sv start celery
        sv start celery_beat
    fi

    echo "Running KoBoCAT container with \`runserver_plus\` debugging application server."
    UWSGI_COMMAND="gosu $UWSGI_USER python manage.py runserver_plus 0:8001"
fi
exec ${UWSGI_COMMAND}
