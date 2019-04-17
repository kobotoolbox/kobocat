# Base image to take care of installing `apt` and `pip` requirements.

FROM kobotoolbox/base-kobos:latest


ENV KOBOCAT_TMP_DIR=/srv/kobocat_tmp \
    # Store editable packages (pulled from VCS repos) in their own directory.
    PIP_EDITABLE_PACKAGES_DIR=/srv/pip_editable_packages \
    UWSGI_USER=wsgi \
    UWSGI_GROUP=wsgi 


###########################
# Install `apt` packages. #
###########################

COPY ./apt_requirements.txt ${KOBOCAT_TMP_DIR}/base_apt_requirements.txt
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y $(cat ${KOBOCAT_TMP_DIR}/base_apt_requirements.txt) && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


###########################
# Install `pip` packages. #
###########################

COPY ./requirements/ ${KOBOCAT_TMP_DIR}/base_requirements/
RUN mkdir -p ${PIP_EDITABLE_PACKAGES_DIR} && \
    pip install --upgrade 'pip>=10,<11' && \
    pip install --src ${PIP_EDITABLE_PACKAGES_DIR}/ -r ${KOBOCAT_TMP_DIR}/base_requirements/base.pip && \
    pip install --src ${PIP_EDITABLE_PACKAGES_DIR}/ -r ${KOBOCAT_TMP_DIR}/base_requirements/s3.pip && \
    rm -rf ~/.cache/pip
