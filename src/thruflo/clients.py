#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python clients to external service APIs.
"""

import logging

from datetime import datetime

import config
import utils

### github oauth client

import oauth2

oauth = oauth2.Client2(
    config.oauth['client_id'],
    config.oauth['client_secret'],
    config.oauth['base_url']
)

### github api client

from github2.client import Github
from github2.commits import Commits
from github2.issues import Issues
from github2.repositories import Repositories
from github2.request import GithubRequest
from github2.users import Users

class GithubRequest2(GithubRequest):
    """Override to enable oauth and default to using SSL.
    """
    
    github_url = "https://github.com"
    
    def __init__(
            self, 
            username=None, 
            api_token=None, 
            access_token=None,
            debug=False
        ):
        self.username = username
        self.api_token = api_token
        self.access_token = access_token
        self.debug = debug
        self.url_prefix = self.url_format % {
            "github_url": self.github_url,
            "api_version": self.api_version,
            "api_format": self.api_format,
        }
        
    
    
    def encode_authentication_data(self, extra_post_data):
        """Try oauth access_token first, fall back 
          on login + api token.
        """
        
        if self.access_token:
            post_data = {
                "access_token": self.access_token
            }
        elif self.username and self.api_token:
            post_data = {
                "login": self.username,
                "token": self.api_token
            }
        else:
            post_data = {}
        post_data.update(extra_post_data)
        return utils.unicode_urlencode(post_data)
        
    
    

class Github2(Github):
    """Override to provide an instance of ``GithubRequest2`` at
      ``self.request``.
    """
    
    def __init__(
            self, 
            username=None, 
            api_token=None, 
            access_token=None, 
            debug=False
        ):
        self.debug = debug
        self.request = GithubRequest2(
            username=username, 
            api_token=api_token,
            access_token=access_token,
            debug=self.debug
        )
        self.issues = Issues(self.request)
        self.users = Users(self.request)
        self.repos = Repositories(self.request)
        self.commits = Commits(self.request)
        
    
    

def github_factory(user=None, access_token=None):
    """Takes a ``model.User`` instance or an ``access_token``
      and returns a ``Github2`` instance.
    """
    
    if user is not None:
        access_token = user.access_token
    elif access_token is None:
        raise ValueError('must provide either a user or an access_token')
    
    logging.warning('faking oauth whilst the scopes are implemented')
    #return Github2(access_token=access_token)
    from secret import github_api_token
    return Github2(username='thruflo', api_token=github_api_token)
    


### Spreedly client

import dependencies.spreedly

# patch ``spreedly.str_to_datetime`` to store UTC.
def str_to_datetime(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')

dependencies.spreedly.str_to_datetime = str_to_datetime

class SpreedlyClient(dependencies.spreedly.Client):
    def get_subscribe_url(self, subscriber_id, plan_id, user_login):
        url = '%s/subscribers/%d/subscribe/%d/%s' % (
            self.base_url, 
            subscriber_id,
            plan_id,
            user_login
        )
        return url.replace('/api/%s' % dependencies.spreedly.API_VERSION, '')
        
    
    

spreedly = SpreedlyClient(
    config.spreedly['spreedly_token'], 
    config.spreedly['site_name']
)
