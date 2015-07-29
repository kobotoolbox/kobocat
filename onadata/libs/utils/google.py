import json

import urllib
import urllib2

# TODO: gdata is deprecated. For OAuth2 authentication it should be replaced
#       by oauth2client.
import gdata.gauth

from django.conf import settings

oauth2_token = gdata.gauth.OAuth2Token(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    scope=' '.join(
        ['https://docs.google.com/feeds/',
         'https://spreadsheets.google.com/feeds/',
         'https://www.googleapis.com/auth/drive.file']),
    user_agent='formhub')

redirect_uri = oauth2_token.generate_authorize_url(
    redirect_uri=settings.GOOGLE_STEP2_URI,
    access_type='offline', approval_prompt='force')


def get_refreshed_token(token):
    data = urllib.urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': token.refresh_token,
        'grant_type': 'refresh_token'})
    request = urllib2.Request(
        url='https://accounts.google.com/o/oauth2/token',
        data=data)
    request_open = urllib2.urlopen(request)
    response = request_open.read()
    request_open.close()
    tokens = json.loads(response)
    token.access_token = tokens['access_token']
    return token

        
