#!/bin/bash
set -e

source /etc/profile

oldpwd=$(pwd)
cd "${KOBOCAT_SRC_DIR}"

mkdir -p "${KOBOCAT_SRC_DIR}/onadata/static"

echo "Collecting static files..."
python manage.py collectstatic -v 0 --noinput
echo "Done"

# `chown` becomes very slow once a fair amount of media has been collected.
#echo "Fixing permissions..."
#chown -R "${UWSGI_USER}" "${KOBOCAT_SRC_DIR}"
#echo "Done."
echo '%%%%%%% NOTICE %%%%%%%'
echo '% To avoid long delays, we no longer reset ownership of media files'
echo '% every time this container starts. If you have trouble with'
echo '% permissions, please run the following command inside the'
echo '% `kobocat` container:'
echo "%	chown -R \"${UWSGI_USER}\" \"${KOBOCAT_SRC_DIR}\""
echo '%%%%%%%%%%%%%%%%%%%%%%'

echo "Syncing to nginx folder..."
rsync -aq ${KOBOCAT_SRC_DIR}/onadata/static/* /srv/static/
echo "Done"

cd $oldpwd
