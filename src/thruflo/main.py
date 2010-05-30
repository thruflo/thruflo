#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI app as ``application``.
"""

from web import WSGIApplication
from urls import mapping

def app_factory():
    return WSGIApplication(mapping)


application = app_factory()
