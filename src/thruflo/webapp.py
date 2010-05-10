#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tornado_ WSGI application.  We use Tornado for its nice web
  framework features, not for its non blocking via callback and
  pycurl "features".
  
  .. _Tornado: http://www.tornadoweb.org
"""

import sys
from os.path import dirname, join as join_path

from tornado import httpserver, ioloop, web
from tornado import options as tornado_options
from tornado.options import define, options

from views import *

define('port', default=8888, help='bind to port')

mapping = [(
        r'^/$', 
        Index,
    ), (
        r'^/login\/?$',
        Login
    ), (
        r'^/logout\/?$',
        Logout
    ), (
        r'^/register\/?$',
        Register
    ), (
        r'^/dashboard\/?$',
        Dashboard
    ), (
        r'^/documents(\/([\w]*))?(\/([\w]*))?\/?$',
        Documents
    ), (
        r'^/projects(\/([\w]*))?(\/([\w]*))?(\/([\w]*))?\/?$',
        Projects
    ), (
        r'^/themes(\/([\w]*))?(\/([\w]*))?\/?$',
        Themes
    ), (
        r'^/deliverables(\/([\w]*))?(\/([\w]*))?(\/([\w]*))?\/?$',
        Deliverables
    ), (
        r'^/.*$',
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
    'xsrf_cookies': True,
    'domain': 'thruflo.com'
}

application = web.Application(mapping, debug=False, **settings)

def main():
    tornado_options.parse_command_line()
    http_server = httpserver.HTTPServer(application)
    http_server.bind(options.port)
    http_server.start() # Forks multiple sub-processes
    ioloop.IOLoop.instance().start()
    


if __name__ == "__main__":
    main()

