FROM nikolaik/python-nodejs:python3.8-nodejs10

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV VIRTUAL_ENV=/opt/venv


ENV KOBOCAT_LOGS_DIR=/srv/logs \
    DJANGO_SETTINGS_MODULE=kobo.settings.prod \
    # The mountpoint of a volume shared with the `nginx` container. Static files will
    #   be copied there.
    NGINX_STATIC_DIR=/srv/static \
    KOBOCAT_SRC_DIR=/srv/src/kobocat \
    BACKUPS_DIR=/srv/backups \
    TMP_PATH=/srv/tmp \
    INIT_PATH=/srv/init

# Install Dockerize.
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz -P /tmp \
    && tar -C /usr/local/bin -xzvf /tmp/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm /tmp/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

##########################################
# Create build directories               #
##########################################

RUN mkdir -p "${NGINX_STATIC_DIR}" && \
    mkdir -p "${KOBOCAT_SRC_DIR}" && \
    mkdir -p "${TMP_PATH}" && \
    mkdir -p "${BACKUPS_DIR}" && \
    mkdir -p "${INIT_PATH}"

##########################################
# Install `apt` packages.                #
##########################################
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -

RUN apt -qq update && \
    apt -qq -y install \
        gdal-bin \
        libproj-dev \
        gettext \
        postgresql-client \
        locales \
        runit-init \
        rsync \
        vim && \
    apt clean && \
        rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

###########################
# Install locales         #
###########################

RUN echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
RUN locale-gen && dpkg-reconfigure locales -f noninteractive

###########################
# Copy KoBoCAT directory  #
###########################

COPY . "${KOBOCAT_SRC_DIR}"

###########################
# Install `pip` packages. #
###########################

RUN virtualenv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install  --quiet --upgrade pip && \
    pip install  --quiet pip-tools
COPY ./dependencies/pip/prod.txt /srv/tmp/pip_dependencies.txt
RUN pip-sync /srv/tmp/pip_dependencies.txt 1>/dev/null && \
    rm -rf ~/.cache/pip

##########################################
# Persist the log and email directories. #
##########################################

RUN mkdir -p "${KOBOCAT_LOGS_DIR}/" "${KOBOCAT_SRC_DIR}/emails" && \
    chown -R "${UWSGI_USER}" "${KOBOCAT_SRC_DIR}/emails/" && \
    chown -R "${UWSGI_USER}" "${KOBOCAT_LOGS_DIR}"

#################################################
# Handle runtime tasks and create main process. #
#################################################

# Using `/etc/profile.d/` as a repository for non-hard-coded environment variable overrides.
RUN echo "export PATH=${PATH}" >> /etc/profile
RUN echo 'source /etc/profile' >> /root/.bashrc

# Prepare for execution.
RUN mkdir -p /etc/service/uwsgi_wrong_port_warning && \
    cp "${KOBOCAT_SRC_DIR}/docker/run_uwsgi_wrong_port_warning.bash" /etc/service/uwsgi_wrong_port_warning/run && \
    mkdir -p /etc/service/uwsgi && \
    # Remove getty* services
    rm -rf /etc/runit/runsvdir/default/getty-tty* && \
    cp "${KOBOCAT_SRC_DIR}/docker/run_uwsgi.bash" /etc/service/uwsgi/run && \
    mkdir -p /etc/service/celery && \
    ln -s "${KOBOCAT_SRC_DIR}/docker/run_celery.bash" /etc/service/celery/run && \
    mkdir -p /etc/service/celery_beat && \
    ln -s "${KOBOCAT_SRC_DIR}/docker/run_celery_beat.bash" /etc/service/celery_beat/run && \

WORKDIR "${KOBOCAT_SRC_DIR}"

# TODO: Remove port 8000, say, at the start of 2021 (see kobotoolbox/kobo-docker#301 and wrong port warning above)
EXPOSE 8001 8000

CMD ["/bin/bash", "-c", "exec ${KOBOCAT_SRC_DIR}/docker/init.bash"]
