# Per kobotoolbox/kobo-docker#301, we have changed the uWSGI port to 8001. This
# provides a helpful message to anyone still trying to use port 8000.
# Based upon
# https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html#the-first-wsgi-application

html_response = b'''
<html>
<head><title>System configuration error</title></head>
<body>
<h1>System configuration error</h1>
<p>Please contact the administrator of this server.</p>
<p style="border: 0.1em solid black; padding: 0.5em">If you are the
administrator of this server: KoBoCAT received this request on port 8000, when
8001 should have been used. Please see
<a href="https://github.com/kobotoolbox/kobo-docker/issues/301">
https://github.com/kobotoolbox/kobo-docker/issues/301</a> for more
information.</p>
<p>Thanks for using KoBoToolbox.</p></body></html>
'''

def application(env, start_response):
    start_response('503 Service Unavailable', [('Content-Type','text/html')])
    return [html_response]
