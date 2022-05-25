#!/bin/bash
set -e

echo 'Waiting for container `mongo`.'
echo '--->' $KOBOCAT_MONGO_HOST
dockerize -timeout=40s -wait tcp://${KOBOCAT_MONGO_HOST}:${KOBOCAT_MONGO_PORT}
echo 'Container `mongo` up.'
