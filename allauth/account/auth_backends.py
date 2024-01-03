from django.contrib.auth.backends import ModelBackend


class AuthenticationBackend(ModelBackend):
    # this class *only* exists because kobocat and kpi need to use the same
    # AUTHENTICATION_BACKEND setting when sharing sessions. kpi uses
    # 'allauth.account.auth_backends.AuthenticationBackend', so we have to fake it
    pass
