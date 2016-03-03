FROM kobotoolbox/base-kobocat:docker_local

MAINTAINER Serban Teodorescu, teodorescu.serban@gmail.com

RUN mkdir -p /etc/service/celery

COPY docker/run_wsgi /etc/service/wsgi/run
COPY docker/run_celery /etc/service/celery/run
COPY docker/*.sh docker/kobocat.ini /srv/src/

# Upgrade `apt` packages.
# RUN apt-get update && \
#    apt-get upgrade -y && \
#    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install post-base-image `apt` additions from `apt_requirements.txt`, if modified.
COPY ./apt_requirements.txt /tmp/kobocat_apt_requirements.txt
RUN diff -q /tmp/kobocat_apt_requirements.txt /srv/src/kobocat/apt_requirements.txt || \
    apt-get update && \
    apt-get install -y $(cat /tmp/kobocat_apt_requirements.txt) && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    || true # Prevent non-zero exit code.  

# Install post-base-image `pip` additions/upgrades from `requirements/base.pip`, if modified.
COPY ./requirements/base.pip /tmp/kobocat_base_requirements.pip
RUN diff -q /tmp/kobocat_base_requirements.pip /srv/src/kobocat/requirements/base.pip || \
    pip install --upgrade -r /tmp/kobocat_base_requirements.pip \
    || true # Prevent non-zero exit code.

# Wipe out the base image's `kobocat` dir (**including migrations**) and copy over this directory in it's live state.
RUN rm -rf /srv/src/kobocat
COPY . /srv/src/kobocat

# `pip` packages installed in the base image that should be removed can be listed in `requirements/uninstall.pip`.
RUN bash -c '[[ -e /srv/src/kobocat/requirements/uninstall.pip ]] && pip uninstall --yes -r /srv/src/kobocat/requirements/uninstall.pip'

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

VOLUME ["/srv/src/kobocat", "/srv/src/kobocat/onadata/media", "/srv/src/kobocat-template", "/tmp"]

WORKDIR /srv/src/kobocat

EXPOSE 8000

CMD ["/sbin/my_init"]
