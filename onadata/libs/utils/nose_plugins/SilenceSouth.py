# coding: utf-8
from nose.plugins import Plugin  # noqa

import logging


class SilenceSouth(Plugin):
    south_logging_level = logging.ERROR

    def configure(self, options, conf):
        super().configure(options, conf)
        logging.getLogger('south').setLevel(self.south_logging_level)
