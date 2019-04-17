FROM kobotoolbox/kobocat_base:latest

ENV KOBOCAT_SRC_DIR=/srv/src/kobocat \
    BACKUPS_DIR=/srv/backups \
    KOBOCAT_LOGS_DIR=/srv/logs

# Install post-base-image `apt` additions from `apt_requirements.txt`, if modified.
COPY ./apt_requirements.txt "${KOBOCAT_TMP_DIR}/current_apt_requirements.txt"
RUN if ! diff "${KOBOCAT_TMP_DIR}/current_apt_requirements.txt" "${KOBOCAT_TMP_DIR}/base_apt_requirements.txt"; then \
        apt-get update && \
        apt-get install -y $(cat "${KOBOCAT_TMP_DIR}/current_apt_requirements.txt") && \
        apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    ; fi

# Version 8 of pip doesn't really seem to upgrade packages when switching from
# PyPI to editable Git
RUN pip install --upgrade 'pip>=10,<11'

# Install post-base-image `pip` additions/upgrades from `requirements/base.pip`, if modified.
COPY ./requirements/ "${KOBOCAT_TMP_DIR}/current_requirements/"
# FIXME: Replace this with the much simpler command `pip-sync ${KOBOCAT_TMP_DIR}/current_requirements/base.pip`.
RUN if ! diff "${KOBOCAT_TMP_DIR}/current_requirements/base.pip" "${KOBOCAT_TMP_DIR}/base_requirements/base.pip"; then \
        pip install --src "${PIP_EDITABLE_PACKAGES_DIR}/" -r "${KOBOCAT_TMP_DIR}/current_requirements/base.pip" \
    ; fi

# Install post-base-image `pip` additions/upgrades from `requirements/s3.pip`, if modified.
RUN if ! diff "${KOBOCAT_TMP_DIR}/current_requirements/s3.pip" "${KOBOCAT_TMP_DIR}/base_requirements/s3.pip"; then \
        pip install --src "${PIP_EDITABLE_PACKAGES_DIR}/" -r "${KOBOCAT_TMP_DIR}/current_requirements/s3.pip" \
    ; fi

# Uninstall `pip` packages installed in the base image from `requirements/uninstall.pip`, if present.
# FIXME: Replace this with the much simpler `pip-sync` command equivalent.
RUN if [ -e "${KOBOCAT_TMP_DIR}/current_requirements/uninstall.pip" ]; then \
        pip uninstall --yes -r "${KOBOCAT_TMP_DIR}/current_requirements/uninstall.pip" \
    ; fi

# Wipe out the base image's `kobocat` dir (**including migration files**) and copy over this directory in its current state.
RUN rm -rf "${KOBOCAT_SRC_DIR}"
COPY . "${KOBOCAT_SRC_DIR}"

# Prepare for execution.
RUN mkdir -p /etc/service/uwsgi && \
    cp "${KOBOCAT_SRC_DIR}/docker/run_uwsgi.bash" /etc/service/uwsgi/run && \
    mkdir -p /etc/service/celery && \
    ln -s "${KOBOCAT_SRC_DIR}/docker/run_celery.bash" /etc/service/celery/run && \
    mkdir -p /etc/service/celery_beat && \
    ln -s "${KOBOCAT_SRC_DIR}/docker/run_celery_beat.bash" /etc/service/celery_beat/run && \
    cp "${KOBOCAT_SRC_DIR}/docker/init.bash" /etc/my_init.d/10_init_kobocat.bash && \
    cp "${KOBOCAT_SRC_DIR}/docker/sync_static.sh" /etc/my_init.d/11_sync_static.bash && \
    mkdir -p "${KOBOCAT_SRC_DIR}/emails/" && \
    chown -R "${UWSGI_USER}" "${KOBOCAT_SRC_DIR}/emails/" && \
    mkdir -p "${BACKUPS_DIR}" && \
    mkdir -p "${KOBOCAT_LOGS_DIR}" && \
    chown -R "${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"

RUN echo "db:*:*:kobo:kobo" > /root/.pgpass && \
    chmod 600 /root/.pgpass

# Using `/etc/profile.d/` as a repository for non-hard-coded environment variable overrides.
RUN echo 'source /etc/profile' >> /root/.bashrc


WORKDIR "${KOBOCAT_SRC_DIR}"

EXPOSE 8000
