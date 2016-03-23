#!/usr/bin/env bash
set -e


export KOBOCAT_SRC_DIR=${KOBOCAT_SRC_DIR:-"$(cd $(dirname $0)/.. && pwd)/"}

echo 'Downloading translations from Transifex.'
(cd ${KOBOCAT_SRC_DIR} && tx pull --all)
# FIXME: Don't pull "pseudo-translations" once we have real translations.
(cd ${KOBOCAT_SRC_DIR} && tx pull --all --pseudo)

echo 'Compiling translations.'
(cd ${KOBOCAT_SRC_DIR} && python manage.py compilemessages)
echo 'Compiliation complete!'
