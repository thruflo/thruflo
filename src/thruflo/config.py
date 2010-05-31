#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Application settings.
"""

import logging
import re
import sys

from os.path import dirname, join as join_path

import secret

# logging setup
if sys.platform == 'darwin':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('beaker').setLevel(logging.INFO)
    logging.getLogger('restkit').setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('beaker').setLevel(logging.WARNING)
    logging.getLogger('restkit').setLevel(logging.WARNING)

# web application settings
settings = {
    'static_path': join_path(dirname(__file__), 'static'),
    'cookie_secret': secret.cookie_secret,
    'login_url': '/login',
    'xsrf_cookies': True,
    'domain': 'thruflo.com'
}

# github oauth settings
oauth = {
    'client_id': '83c01f987ff4b78c6648',
    'client_secret': secret.github_client_secret,
    'base_url': 'https://github.com/login/oauth/',
    'redirect_url': 'http://dev.thruflo.com/oauth/callback'
}

# spreedly access settings
spreedly = {
    'site_name': 'thruflo-test',
    'free_trial_plan_id': 5883,
    'paid_plan_id': 5680,
    'spreedly_token': secret.spreedly_token
}
