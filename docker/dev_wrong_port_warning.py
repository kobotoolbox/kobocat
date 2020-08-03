#!/usr/bin/env python

"""
Per kobotoolbox/kobo-docker#301, we have changed the uWSGI port to 8001. This
provides a helpful message to anyone still trying to use port 8000
"""

import BaseHTTPServer
import sys

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(503)
        self.end_headers()
        self.wfile.write(
            'Your development environment is trying to connect to the KoBoCAT '
            'container on port 8000 instead of 8001. Please change this. See '
            'https://github.com/kobotoolbox/kobo-docker/issues/301 '
            'for more details.'
        )

server_address = ('', int(sys.argv[1]))
httpd = BaseHTTPServer.HTTPServer(server_address, Handler)
httpd.serve_forever()
