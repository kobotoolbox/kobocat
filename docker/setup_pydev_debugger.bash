#!/bin/bash
set -e

# Keep it as is, not tested with Python3
rm -rf /etc/profile.d/pydev_debugger.bash.sh
if [[ -d /srv/pydev_orig && -n "${KOBOCAT_PATH_FROM_ECLIPSE_TO_PYTHON_PAIRS}" ]]; then
    echo 'Enabling PyDev remote debugging.'
    "${KOBOCAT_SRC_DIR}/docker/setup_pydev.bash"
fi
