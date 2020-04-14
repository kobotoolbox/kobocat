# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import


class RestServiceInterface(object):
    def send(self, url, data=None):
        raise NotImplementedError
