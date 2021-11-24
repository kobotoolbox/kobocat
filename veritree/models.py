from django.contrib.auth.backends import ModelBackend

class VeritreeOAuth2(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        """
        Authentication should happen through kpi anyways, this will be here simply for session
        validation
        """
        return None
