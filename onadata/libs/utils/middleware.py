# coding: utf-8

from django.db import connection
from django.http import HttpResponseNotAllowed
from django.template import loader
from django.middleware.locale import LocaleMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation.trans_real import parse_accept_lang_header


class HTTPResponseNotAllowedMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        if isinstance(response, HttpResponseNotAllowed):
            response.content = loader.render_to_string(
                "405.html", request=request)

        return response


class LocaleMiddlewareWithTweaks(LocaleMiddleware):
    """
    Overrides LocaleMiddleware from django with:
        Khmer `km` language code in Accept-Language is rewritten to km-kh
    """

    def process_request(self, request):
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        try:
            codes = [code for code, r in parse_accept_lang_header(accept)]
            if 'km' in codes and 'km-kh' not in codes:
                request.META['HTTP_ACCEPT_LANGUAGE'] = accept.replace('km',
                                                                      'km-kh')
        except:
            # this might fail if i18n is disabled.
            pass

        super(LocaleMiddlewareWithTweaks, self).process_request(request)


class SqlLogging(MiddlewareMixin):
    def process_response(self, request, response):
        from sys import stdout
        if stdout.isatty():
            for query in connection.queries:
                print("\033[1;31m[%s]\033[0m \033[1m%s\033[0m" % (
                    query['time'], " ".join(query['sql'].split())))

        return response


class UsernameInResponseHeaderMiddleware(MiddlewareMixin):
    """
    Record the authenticated user (if any) in the `X-KoBoNaUt` HTTP header
    """
    def process_response(self, request, response):
        try:
            user = request.user
        except AttributeError:
            return response
        if user.is_authenticated:
            response['X-KoBoNaUt'] = request.user.username
        return response
