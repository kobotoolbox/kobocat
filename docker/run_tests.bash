#!/usr/bin/env bash
set -e
source /etc/profile

echo "print('Django shell loaded successfully.')" | python manage.py shell
