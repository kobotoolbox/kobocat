#!/usr/bin/env bash
set -e


KOBOCAT_DIR=${KOBOCAT_DIR:-"$(cd $(dirname $0)/.. && pwd)/"}

echo 'Extracting translatable strings from `kobocat`.'
bash -c "cd ${KOBOCAT_DIR} && python manage.py makemessages --locale en"

# FIXME: Remove this workaround for `kobocat-template` translatable strings ...eventually.
echo 'Backing up translatable strings from `kobocat`.'
mv ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/django.po ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/kobocat.po
echo 'Extracting translatable strings from `kobocat-template`.'
KOBOCAT_TEMPLATES_DIR=${KOBOCAT_TEMPLATES_DIR:-"$( dirname ${KOBOCAT_DIR} )/kobocat-template/"}
bash -c "cd ${KOBOCAT_TEMPLATES_DIR} && python ${KOBOCAT_DIR}/manage.py makemessages --locale en"
mv ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/django.po ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/kobocat-template.po
echo 'Merging translatable strings from `kobocat` and `kobocat-template`.'
msgcat ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/{kobocat.po,kobocat-template.po} -o ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/django.po
rm ${KOBOCAT_DIR}/locale/en/LC_MESSAGES/{kobocat.po,kobocat-template.po}

echo 'Pushing translatable strings to Transifex.'
tx push -s

echo 'Pulling latest translations from Transifex.'
tx pull --all
# FIXME: Remove use of Transifex's "pseudo" translations once we have real translations.
tx pull --pseudo --all

echo 'Compiling translations'
bash -c "cd ${KOBOCAT_DIR} && python manage.py compilemessages"
