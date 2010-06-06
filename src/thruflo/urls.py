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
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/?$',
        view.Repository
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/doc\/add\/?$',
        view.AddDocument
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/doc\/([0-9]{8})\/?$',
        view.Document
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/get_blobs\/?$',
        view.GetBlobs
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/doc\/([0-9]{8})\/insert\/?$',
        view.InsertBlob
    ), (
        r'^/repo\/([-\.\w]*)\/([-\.\w]*)\/doc\/([0-9]{8})\/listen\/?$',
        view.ListenForUpdates
    ), (
        r'^/hooks/post_commit\/?$',
        view.PostCommitHook
    )
]
