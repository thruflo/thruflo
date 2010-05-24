#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Patch libs.  This module should always be imported first.
"""

# patch sockets, threading etc. so they don't block
from gevent import monkey
monkey.patch_all()

# patch github library to use https by default
import github2.request
github2.request.GITHUB_URL = "https://github.com"
github2.request.URL_PREFIX = "https://github.com/api/v2/json"
