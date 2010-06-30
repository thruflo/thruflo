#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mapping of URLs to ``view.RequestHandler``s.
"""

from schema import slug_pattern as slug
from schema import username_pattern as username

import view

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
        r'^/%s\/%s\/?$' % (username, slug),
        view.Editor
    ), (
        r'^/%s\/%s\/(create|overwrite|rename|delete|fetch|listen)\/?$' % (username, slug),
        view.Editor
    ),(
        r'^/bespin\/?',
        view.Bespin
    )
]
