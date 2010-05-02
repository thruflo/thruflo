#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Daemonizes a process, e.g.:
  
  ``daemonize.py ./log/close-serve.pid ./bin/close-serve``
  
  Will daemonize ``./bin/close-serve`` and store the pid in 
  ``./log/close-serve.pid``
  
  See http://bit.ly/c15l9j for details.
"""

import sys, os
from grizzled.os import spawnd

def main():
    pidfile = os.path.abspath(sys.argv[1])
    path = os.path.abspath(sys.argv[2])
    args = sys.argv[2:]
    sys.exit(
        spawnd(path, args, pidfile=pidfile)
    )
    


if __name__ == '__main__':
    main()

