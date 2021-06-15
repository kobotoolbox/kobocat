#!/usr/bin/env python
# coding: utf-8
import logging
import os
import sys

if __name__ == "__main__":
    # altered for new settings layout
    if not any([arg.startswith('--settings=') for arg in sys.argv]):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                              "onadata.settings.base")
        print('Your environment is:"{}"'.format(
            os.environ['DJANGO_SETTINGS_MODULE']))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
