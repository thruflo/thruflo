#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Application settings.
"""

from os.path import dirname, join as join_path
import secret

settings = {
    'static_path': join_path(dirname(__file__), 'static'),
    'cookie_secret': secret.cookie_secret,
    'login_url': '/login',
    'xsrf_cookies': True,
    'domain': 'thruflo.com'
}
