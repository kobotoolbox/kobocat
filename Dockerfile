FROM kobotoolbox/base-kobocat:docker_local

MAINTAINER Serban Teodorescu, teodorescu.serban@gmail.com

RUN mkdir -p /etc/service/celery

COPY docker/run_wsgi /etc/service/wsgi/run
COPY docker/run_celery /etc/service/celery/run
COPY docker/*.sh docker/kobocat.ini /srv/src/

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

VOLUME ["/srv/src/kobocat", "/srv/src/kobocat/onadata/media", "/srv/src/kobocat-template", "/tmp"]

EXPOSE 8000

CMD ["/sbin/my_init"]
