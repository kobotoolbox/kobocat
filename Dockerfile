FROM kobotoolbox/kobocat_base:latest

RUN mkdir -p /etc/service/celery

COPY docker/run_wsgi /etc/service/wsgi/run
COPY docker/run_celery /etc/service/celery/run
COPY docker/*.sh docker/kobocat.ini /srv/src/

# Install post-base-image `apt` additions from `apt_requirements.txt`, if modified.
COPY ./apt_requirements.txt /srv/tmp/kobocat_apt_requirements.txt
RUN diff -q /srv/tmp/kobocat_apt_requirements.txt /srv/tmp/kobocat_base_apt_requirements.txt || \
    apt-get update && \
    apt-get install -y $(cat /srv/tmp/kobocat_apt_requirements.txt) && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    || true # Prevent non-zero exit code.  

# Install post-base-image `pip` additions/upgrades from `requirements/base.pip`, if modified.
COPY ./requirements/ /srv/tmp/kobocat_requirements/
# FIXME: Replace this with the much simpler command `pip-sync /srv/tmp/kobocat_requirements/base.pip`.
RUN diff -q /srv/tmp/kobocat_requirements/base.pip /srv/tmp/kobocat_base_requirements/base.pip || \
    pip install --src ${PIP_EDITABLE_PACKAGES_DIR}/ -r /srv/tmp/kobocat_requirements/base.pip \
    || true # Prevent non-zero exit code.

# Uninstall `pip` packages installed in the base image from `requirements/uninstall.pip`, if present.
# FIXME: Replace this with the much simpler `pip-sync` command.
COPY ./requirements/ /srv/src/kobocat/requirements/
RUN bash -c '[[ -e /srv/src/kobocat/requirements/uninstall.pip ]] && \
    pip uninstall --yes -r /srv/src/kobocat/requirements/uninstall.pip' \
    || true  # Prevent non-zero status code when there's nothing to uninstall.

# Wipe out the base image's `kobocat` dir (**including migration files**) and copy over this directory in its live state.
RUN rm -rf /srv/src/kobocat
COPY . /srv/src/kobocat

RUN chmod +x /etc/service/wsgi/run && \
    chmod +x /etc/service/celery/run && \
    echo "db:*:*:kobo:kobo" > /root/.pgpass && \
    chmod 600 /root/.pgpass

# Using `/etc/profile.d/` as a repository for non-hard-coded environment variable overrides.
RUN echo 'source /etc/profile' >> /root/.bashrc

COPY ./docker/init.bash /etc/my_init.d/10_init_kobocat.bash
COPY ./docker/sync_static.sh /etc/my_init.d/11_sync_static.bash
RUN mkdir -p /srv/src/kobocat/emails/ && \
    chown -R wsgi /srv/src/kobocat/emails/

VOLUME ["/srv/src/kobocat", "/srv/src/kobocat/onadata/media", "/srv/src/kobocat-template"]

WORKDIR /srv/src/kobocat

EXPOSE 8000

CMD ["/sbin/my_init"]
