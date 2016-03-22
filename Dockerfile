FROM kobotoolbox/kobocat_base:latest

RUN mkdir -p /etc/service/celery

COPY docker/run_wsgi /etc/service/wsgi/run
COPY docker/run_celery /etc/service/celery/run
COPY docker/*.sh docker/kobocat.ini /srv/src/

# Install post-base-image `apt` additions from `apt_requirements.txt`, if modified.
COPY ./apt_requirements.txt ${KOBOCAT_TMP_DIR}/current_apt_requirements.txt
RUN diff -q ${KOBOCAT_TMP_DIR}/current_apt_requirements.txt ${KOBOCAT_TMP_DIR}/base_apt_requirements.txt || \
    apt-get update && \
    apt-get install -y $(cat ${KOBOCAT_TMP_DIR}/current_apt_requirements.txt) && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    || true # Prevent non-zero exit code.  

# Install post-base-image `pip` additions/upgrades from `requirements/base.pip`, if modified.
COPY ./requirements/ ${KOBOCAT_TMP_DIR}/current_requirements/
# FIXME: Replace this with the much simpler command `pip-sync ${KOBOCAT_TMP_DIR}/current_requirements/base.pip`.
RUN diff -q ${KOBOCAT_TMP_DIR}/current_requirements/base.pip ${KOBOCAT_TMP_DIR}/base_requirements/base.pip || \
    pip install --src ${PIP_EDITABLE_PACKAGES_DIR}/ -r ${KOBOCAT_TMP_DIR}/current_requirements/base.pip \
    || true # Prevent non-zero exit code.

# Uninstall `pip` packages installed in the base image from `requirements/uninstall.pip`, if present.
# FIXME: Replace this with the much simpler `pip-sync` command.
RUN bash -c '[[ -e ${KOBOCAT_TMP_DIR}/current_requirements/uninstall.pip ]] && \
    pip uninstall --yes -r ${KOBOCAT_TMP_DIR}/current_requirements/uninstall.pip' \
    || true  # Prevent non-zero status code when there's nothing to uninstall.

# Wipe out the base image's `kobocat` dir (**including migration files**) and copy over this directory in its current state.
RUN rm -rf ${KOBOCAT_SRC_DIR}
COPY . ${KOBOCAT_SRC_DIR}

RUN chmod +x /etc/service/wsgi/run && \
    chmod +x /etc/service/celery/run && \
    echo "db:*:*:kobo:kobo" > /root/.pgpass && \
    chmod 600 /root/.pgpass

# Using `/etc/profile.d/` as a repository for non-hard-coded environment variable overrides.
RUN echo 'source /etc/profile' >> /root/.bashrc

COPY ./docker/init.bash /etc/my_init.d/10_init_kobocat.bash
COPY ./docker/sync_static.sh /etc/my_init.d/11_sync_static.bash
RUN mkdir -p ${KOBOCAT_SRC_DIR}/emails/ && \
    chown -R wsgi ${KOBOCAT_SRC_DIR}/emails/

VOLUME ["${KOBOCAT_SRC_DIR}", "${KOBOCAT_SRC_DIR}/onadata/media", "/srv/src/kobocat-template"]

WORKDIR ${KOBOCAT_SRC_DIR}

EXPOSE 8000

CMD ["/sbin/my_init"]
