# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from nose.plugins import Plugin  # noqa

import logging


class SilenceSouth(Plugin):
    south_logging_level = logging.ERROR

    def configure(self, options, conf):
        super(SilenceSouth, self).configure(options, conf)
        logging.getLogger('south').setLevel(self.south_logging_level)
