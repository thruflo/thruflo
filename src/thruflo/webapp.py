#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tornado_ wsgi application.  We use Tornado only for its nice wsgi,
  static file, xsrf and secure cookie features.
  
  .. _Tornado: http://www.tornadoweb.org
"""

## patch tornado's httpclient to use ...
#import tornado.httpclient
#tornado.httpclient.AsyncHTTPClient = <...>.AsyncHTTPClient

import wsgiref.simple_server

from tornado import web, wsgi
from tornado import options as tornado_options
from tornado.options import define, options

from utils import do_nothing
from views import *

define('port', default=8888, help='bind to port')
define('debug', default=False, help='debug mode')

mapping = [(
        r'/', 
        Index,
    ), (
        r'/login\/?', 
        Login
    ), (
        r'/.*',
        NotFound
    )
]

settings = {
    'static_path': join_path(
        dirname(__file__), 
        'static'
    ),
    'cookie_secret': 'ONqi04WSTsqnYjznTRZeH3d5lhi6pULqiGgRdGy9GIE=',
    'login_url': '/login',
    'xsrf_cookies': True
}

application = wsgi.WSGIApplication(mapping, debug=False, **settings)

def main():
    tornado_options.enable_pretty_logging = do_nothing
    tornado_options.parse_command_line()
    server = wsgiref.simple_server.make_server(
        '', 
        options.port, 
        application
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    


if __name__ == "__main__":
    main()

