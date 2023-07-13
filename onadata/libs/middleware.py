from typing import Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.template.loader import get_template
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as t
from kobo_service_account.models import ServiceAccountUser

from onadata.libs.http import JsonResponseForbidden, XMLResponseForbidden


ALLOWED_VIEWS_WITH_WEAK_PASSWORD = {
    'XFormListApi': {
        'actions': {
            'GET': ['manifest', 'media', 'list',  'retrieve'],
        }
    },
    'XFormSubmissionApi': {
        'actions': {
            'POST': ['create'],
        }
    },
    'RedirectView': {
        'view_initkwargs': [
            '/static/images/favicon.ico'
        ]
    },
}


class RestrictedAccessMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        super().__init__(get_response)
        self._allowed_view = None

    def process_response(self, request, response):
        if not request.user.is_authenticated:
            return response

        if isinstance(request.user, ServiceAccountUser):
            return response

        try:
            profile = request.user.profile
        except get_user_model().profile.RelatedObjectDoesNotExist:
            # Consider user's password as weak
            if not self._allowed_view:
                return self._render_response(response)

        if profile.validated_password:
            return response

        if not self._allowed_view:
            return self._render_response(response)

        return response

    def process_view(self, request, view, view_args, view_kwargs):
        """
        Validate if view is among allowed one with unsafe password.
        If it is not, set `self._allowed_view` to False to alter the
        response in `process_response()`.

        We cannot validate user's password here because DRF authentication
        takes places after this method call. Thus, `request.user` is always
        anonymous if user is authenticated with something else than the session.
        """
        view_name = view.__name__

        # Reset boolean for each processed view
        self._allowed_view = True

        if hasattr(view, 'actions'):
            # Allow HEAD requests all the time
            if request.method == 'HEAD':
                return

            try:
                allowed_actions = ALLOWED_VIEWS_WITH_WEAK_PASSWORD[view_name][
                    'actions'
                ][request.method]
            except KeyError:
                self._allowed_view = False
                return

            view_action = view.actions[request.method.lower()]
            if view_action not in allowed_actions:
                self._allowed_view = False
                return

        if hasattr(view, 'view_initkwargs'):
            try:
                allowed_urls = ALLOWED_VIEWS_WITH_WEAK_PASSWORD[view_name][
                    'view_initkwargs'
                ]
            except KeyError:
                self._allowed_view = False
                return

            url = view.view_initkwargs['url']
            if url not in allowed_urls:
                self._allowed_view = False
                return

        return

    def _render_response(
        self, response
    ) -> Union[
        HttpResponseForbidden, JsonResponseForbidden, XMLResponseForbidden
    ]:
        """
        Render response in the requested format: HTML, JSON or XML.
        If content type is not detected, fallback on HTML.
        """
        template = get_template('restricted_access.html')
        format_ = None
        try:
            content_type, *_ = response.accepted_media_type.split(';')
        except AttributeError:
            pass
        else:
            *_, format_ = content_type.split('/')

        if format_ not in ['xml', 'json']:
            return HttpResponseForbidden(template.render())
        else:
            data = {
                'detail': t(
                    f'Your access is restricted. Please reclaim your access by '
                    f'changing your password at '
                    f'{settings.KOBOFORM_URL}/accounts/password/reset/.'
                )
            }
            if format_ == 'json':
                return JsonResponseForbidden(data)
            else:
                return XMLResponseForbidden(
                    data, renderer_context=response.renderer_context
                )
