#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Mapping of URLs to ``view.RequestHandler``s.
"""

import view

mapping = [(
        r'^/$', 
        view.Index,
    ), (
        r'^/login\/?$',
        view.OAuthLogin
    ), (
        r'^/oauth\/callback\/?$',
        view.OAuthCallback
    ), (
        r'^/logout\/?$',
        view.Logout
    ), (
        r'^/dashboard\/?$',
        view.Dashboard
    #), (
    #    r'^/repositories(\/([\w]*))?(\/([\w]*))?\/?$',
    #    view.Repositories
    #), (
    #    r'^/documents(\/([\w]*))?(\/([\w]*))?\/?$',
    #    view.Documents
    ), (
        r'^/hooks/post_commit\/([a-z0-9]{32})\/?$',
        view.PostCommitHook
    )
]

