#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI app factory as ``app_factory()`` and
  ``main()`` which preforks one per detected cpu core.
"""

import patch

from gevent import fork, wsgi

import os
import sys

import view
import web

mapping = [(
        r'^/$', 
        view.Index,
    ), (
        r'^/login\/?$',
        view.Login
    ), (
        r'^/logout\/?$',
        view.Logout
    ), (
        r'^/register\/?$',
        view.Register
    ), (
        r'^/dashboard\/?$',
        view.Dashboard
    ), (
        r'^/repositories(\/([\w]*))?(\/([\w]*))?\/?$',
        view.Repositories
    ), (
        r'^/documents(\/([\w]*))?(\/([\w]*))?\/?$',
        view.Documents
    ), (
        r'^/stylesheets(\/([\w]*))?(\/([\w]*))?\/?$',
        view.Stylesheets
    ), (
        r'^/hooks/post_commit\/?$',
        view.PostCommitHook
    )
]

def app_factory():
    return web.WSGIApplication(mapping)
    


def main():
    num_processes = _cpu_count()
    for i in range(num_processes):
        if fork() == 0:
            try:
                wsgi.WSGIServer(('', 6543 + i), app_factory()).serve_forever()
            except KeyboardInterrupt:
                pass
            return
    try:
        os.waitpid(-1, 0)
    except KeyboardInterrupt:
        pass
    


def _cpu_count(default=2):
    """Returns the number of CPUs in the system.
    """
    
    if sys.platform == 'darwin':
        try:
            num = int(os.popen('sysctl -n hw.ncpu').read())
        except ValueError:
            num = 0
    else:
        try:
            num = os.sysconf('SC_NPROCESSORS_ONLN')
        except (ValueError, OSError, AttributeError):
            num = 0
    return num >= 1 and num or default
    


if __name__ == '__main__':
    main()

