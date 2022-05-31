# coding: utf-8
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from onadata import koboform
from onadata.libs.utils.user_auth import helper_auth_helper

# Always redirect to user profile,
# regardless of koboform setting
DISABLED_VIEWS = [
    'home',
]

# if user not logged in:
#   if kform server exists: redirect to kform login url
#   else: redirect to kc login url
REDIRECT_IF_NOT_LOGGED_IN = [
    'profile',
    'home',
    'download_xlsform',
]

# Misc behavior
#   /accounts/login/     => kform/accounts/login
#   /accounts/logout/    => kform/accounts/logout
#   /accounts/register/  => kform/accounts/register


class ConditionalRedirects(MiddlewareMixin):

    def process_view(self, request, view, args, kwargs):
        view_name = view.__name__
        if request.user.is_anonymous:
            helper_auth_helper(request)
        is_logged_in = request.user.is_authenticated
        login_url = reverse('login')
        if koboform.active and koboform.autoredirect:
            login_url = koboform.redirect_url(login_url)
            if view_name == 'login':
                return HttpResponseRedirect(
                    koboform.login_url(next_kobocat_url='/')
                )
            if view_name == 'logout':
                return HttpResponseRedirect(
                    koboform.redirect_url('/accounts/logout/')
                )

        if view_name in DISABLED_VIEWS:
            if is_logged_in:
                redirect_to = reverse(
                    'user_profile', kwargs={'username': request.user.username}
                )
            else:
                if koboform.active and koboform.autoredirect:
                    redirect_to = koboform.login_url(next_kobocat_url=request.path)
                else:
                    redirect_to = login_url
            return HttpResponseRedirect(redirect_to)
        elif not is_logged_in and (view_name in REDIRECT_IF_NOT_LOGGED_IN):
            return HttpResponseRedirect(login_url)
        pass
