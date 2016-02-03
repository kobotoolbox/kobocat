#!/bin/bash

oldpwd=$(pwd)
cd /srv/src/kobocat

[ -e /tmp/computed_vars.source.bash ] && source /tmp/computed_vars.source.bash
 
python manage.py syncdb --noinput

python manage.py migrate --noinput

cd $oldpwd
