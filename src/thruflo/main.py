#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provide a WSGI app factory that monkey patches
  stdlib with gevent.
"""

import bobo
import os
import sys

from gevent import fork, monkey, wsgi

def app_factory():
    monkey.patch_all()
    return bobo.Application(bobo_resources='thruflo.view')
    


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

