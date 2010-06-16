#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI app as ``application``.
"""

from webapp.web import WSGIApplication

from config import settings
from urls import mapping

def app_factory():
    return WSGIApplication(mapping, settings=settings)

application = app_factory()
