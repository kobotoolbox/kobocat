# coding: utf-8
class RestServiceInterface(object):
    def send(self, url, data=None):
        raise NotImplementedError
