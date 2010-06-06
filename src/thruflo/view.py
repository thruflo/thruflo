#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers.
"""

import functools
import logging
import sys
import time
import urllib2

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

import gevent

import formencode
import webob

import oauth2
from github2.client import Github

from couchdbkit.exceptions import BulkSaveError
from couchdbkit import ResourceNotFound, ResourceConflict

import clients
import config
import model
import schema
import web
import utils

from cache import Redis

def _get_redirect_url(handler):
    redirect_url = None
    if not handler.current_user:
        logging.debug('not authenticated')
        redirect_url = handler.settings['login_url']
        if "?" not in redirect_url:
            redirect_url += "?" + utils.unicode_urlencode(
                dict(next=handler.request.path)
            )
    else:
        user = handler.current_user
        logging.debug(user)
        if not bool(user.sub_level and user.sub_expires > datetime.utcnow()):
            logging.debug('subscription expired')
            # log the user out to 'uncache' the authenticated user
            domain = '.%s' % handler.settings['domain']
            next = handler.get_argument('next', '/')
            handler.clear_cookie('user_id', domain=domain)
            # send them to spreedly to reenergise their subscription
            redirect_url = clients.spreedly.get_subscribe_url(
                int(user.id),
                config.spreedly['paid_plan_id'], 
                user.login
            )
    return redirect_url
    

def subscribed(method):
    """Users accessing methods decorated with ``@subscribed``
      must be authenticated and have an active subscription.
    """
    
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        redirect_url = _get_redirect_url(self)
        if redirect_url is not None:
            if self.request.method == "GET":
                return self.redirect(redirect_url)
            return self.error(403)
        return method(self, *args, **kwargs)
        
    
    return wrapper
    

def restricted(method):
    """Users accessing methods decorated with ``@restricted``
      must be @subscribed and have access to self.repository.
    """
    
    @functools.wraps(method)
    def wrapper(self, repo_owner, repo_name, *args, **kwargs):
        redirect_url = _get_redirect_url(self)
        if redirect_url is not None:
            if self.request.method == "GET":
                return self.redirect(redirect_url)
            return self.error(403)
        else:
            repo_path = '%s/%s' % (repo_owner, repo_name)
            if not bool(repo_path in self.current_user.repositories):
                return self.error(403)
        return method(self, repo_owner, repo_name, *args, **kwargs)
        
    
    return wrapper
    


class RequestHandler(web.RequestHandler):
    """Provides self.request, default implementations for ``self.account``
      and ``self.current_user``, ``self.redirect()`` and 
      ``self.redirect_to_dashboard()``.
    """
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        logging.debug('user_id: %s' % user_id)
        if user_id:
            try:
                user = model.User.get(user_id)
            except ResourceNotFound:
                pass
            else:
                logging.debug('user: %s' % user)
                return user
        return None
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        return self.render_template('index.tmpl')
        
    
    

class OAuthLogin(RequestHandler):
    def get(self):
        redirect_url = self.request.path_url.replace('/login', '/oauth/callback')
        authorization_url = clients.oauth.authorization_url(
            redirect_uri=redirect_url,
            params={
                'scopes': 'user,public_repos,repos,gists'
            }
        )
        logging.debug('authorization_url: %s' % authorization_url)
        return self.redirect(authorization_url)
        
    
    

class OAuthCallback(RequestHandler):
    """Complete the oauth handshale by accepting a ``code``
      and requesting an ``access_token``.
      
      Then get the user's data from github, check their spreedly
      subscription status, ensure we've saved an uptodate 
      ``model.User`` instance and store their ``user_id`` in a 
      secure cookie.
    """
    
    def get(self):
        logging.debug('/oauth/callback')
        code = self.get_argument('code')
        redirect_url = self.request.path_url
        # user logs in
        data = clients.oauth.access_token(code, redirect_url)
        access_token = data.get('access_token')
        logging.debug('access_token: %s' % access_token)
        # get data including `user_data['id']`
        github = clients.github_factory(access_token=access_token)
        user_data = github.request.make_request('user/show').get('user')
        user_id = str(user_data['id'])
        logging.debug('user_id: %s' % user_id)
        # we `get_or_create_and_subscribe_to_free_plan` the subscriber by `id`
        sub = clients.spreedly.get_or_create_subscriber(
            user_data['id'], 
            user_data['login']
        )
        logging.debug('sub')
        logging.debug(sub)
        # they're not subscribed to a plan sign them up the the free trial
        if sub['name'] == '' and sub['trial_elegible']:
            logging.debug('signing user up for a free trial')
            sub = clients.spreedly.subscribe(
                user_data['id'],
                config.spreedly['free_trial_plan_id'],
                trial=True
            )
        # `get_or_create` their `model.User` instance by `id`
        sub_level = 'none'
        if sub['trial_active']:
            sub_level = 'trial'
        elif sub['feature_level']:
            sub_level = sub['feature_level']
        logging.debug('sub_level: %s' % sub_level)
        params = {
            'name': user_data['name'],
            'login': user_data['login'],
            'email': user_data['email'],
            'location': user_data['location'],
            'gravatar_id': user_data['gravatar_id'],
            'sub_level': sub_level,
            'sub_expires': sub['active_until'],
            'access_token': access_token
        }
        user = model.User.get_or_create(docid=user_id, **params)
        # making sure the data we have is uptodate
        changed = False
        for k, v in params.iteritems():
            if v != getattr(user, k):
                changed = True
                setattr(user, k, v)
        if changed:
            logging.debug('user changed')
            user.save()
        # `set_secure_cookie`, either expiring before their next payment
        # or not setting the expires if that's already passed
        if user.sub_expires < datetime.utcnow():
            expires = None
        else:
            expires = sub['active_until']
        self.set_secure_cookie(
            'user_id', user_id,
            domain='.%s' % self.settings['domain'],
            expires_days=None,
            expires=expires
        )
        logging.debug('user authenticated, redirecting...')
        # redirect to a page which will validate their subscription status
        return self.redirect(
            self.get_argument('next', '/dashboard')
        )
        
    
    

class Logout(RequestHandler):
    """Clear cookie and redirect.
    """
    
    def get(self):
        domain = '.%s' % self.settings['domain']
        next = self.get_argument('next', '/')
        self.clear_cookie('user_id', domain=domain)
        return self.redirect(next)
        
    
    

class Dashboard(RequestHandler):
    """
    """
    
    @property
    def repositories(self):
        """Atm this updates repo listing from github every time
          the page is called.
        """
        
        if not hasattr(self, '_repositories'):
            repositories = self.current_user.get_github_repositories()
            self._repositories = repositories
        return self._repositories
        
    
    
    @subscribed
    def get(self):
        return self.render_template('dashboard.tmpl')
        
    
    

class Repository(RequestHandler):
    """@@ ``repository`` contains some magic invalidation.
    """
    
    @property
    def documents(self):
        """
        """
        
        if not hasattr(self, '_documents'):
            self._documents = model.Document.view(
                'all/repo_type_slug_mod',
                startkey=[self.repository.id, 'Document', None, None],
                endkey=[self.repository.id, 'Document', [], []],
                include_docs=True
            ).all()
        return self._documents
        
    
    
    @property
    def repository(self):
        """
        """
        
        if not hasattr(self, '_repository'):
            repository = model.Repository.get_or_create_from(
                self.owner, 
                self.name
            )
            github = clients.github_factory(user=self.current_user)
            repository.update_all(github)
            self._repository = repository
        return self._repository
        
    
    
    @restricted
    def get(self, owner, name):
        self.owner = owner
        self.name = name
        return self.render_template('repository.tmpl', errors={})
        
    
    

class AddDocument(Repository):
    
    params = ['display_name']
    schema = schema.AddOrEditDocument
    
    @restricted
    def post(self, owner, name):
        """``/repo/{owner}/{name}/doc/add``
        """
        
        logging.debug('doc/add')
        
        self.owner = owner
        self.name = name
        
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return self.render_template(
                'repository.tmpl', 
                errors=err.unpack_errors()
            )
        else:
            logging.debug('valid')
            repository_id = model.Repository.get_id_from(
                '%s/%s' % (owner, name)
            )
            params['repository'] = repository_id
            params['slug'] = model.Document.get_unique_slug(repository_id)
            doc = model.Document(**params)
            doc.save()
            return self.redirect(
                '/repo/%s/%s/doc/%s' % (
                    owner, 
                    name, 
                    doc.slug
                )
            )
        
    
    
    def get(self, *args):
        return self.error(405)
        
    
    

class Document(Repository):
    """@@ rendering the page clears the current user's 
      live update queue.
    """
    
    @property
    def blobs(self):
        if not hasattr(self, '_blobs'):
            document = self.document
            github = clients.github_factory(user=self.current_user)
            blobs = document.get_blobs(github)
            self._blobs = blobs
        return self._blobs
        
    
    
    @property
    def document(self):
        if not hasattr(self, '_document'):
            repository_id = model.Repository.get_id_from(
                '%s/%s' % (self.owner, self.name)
            )
            document = model.Document.get_from_slug(repository_id, self.slug)
            self._document = document
        return self._document
        
    
    
    @restricted
    def get(self, owner, name, slug):
        self.owner = owner
        self.name = name
        self.slug = slug
        if self.document:
            redis = Redis(namespace='%s/%s' % (owner, name))
            del redis[self.current_user.id]
            return self.render_template('document.tmpl')
        else:
            return self.error(404)
        
        
    
    

class GetBlobs(Repository):
    """Fetch blob data by id.
    """
    
    @restricted
    def get(self, owner, name):
        """Takes a list of Blob ids via a ``blobs`` param and returns
          a dictionary of {blobid: data, ...}
        """
        
        raise NotImplementedError('@@ get blob content in greenlets')
        
        self.owner = owner
        self.name = name
        
        data = {}
        blobs = []
        
        blob_ids = self.get_arguments('keys[]')
        
        logging.debug('blob_ids')
        logging.debug(blob_ids)
        
        blob_ids = list(set(blob_ids))
        
        # validate
        for item in blob_ids:
            if not schema.valid_blob_id.match(item):
                blob_ids.remove(item)
        
        # fetch
        if blob_ids:
            blobs = model.Blob.view(
                '_all_docs',
                keys=blob_ids,
                include_docs=True
            ).all()
        
        # restrict access
        for item in blobs:
            if not item.repo == self.repository.path:
                blobs.remove(item)
            
        if blobs:
            github = clients.github_factory(user=self.current_user)
            for item in blobs:
                data[item.id] = item.get_data(github)
            
        return data
        
    
    

class InsertBlob(Document):
    """
    """
    
    def insert(self):
        params = {
            'repo': self.repository.path,
            'branch': self.get_argument('branch', None),
            'path': self.get_argument('path', None),
            'index': self.get_argument('index', -1)
        }
        try:
            params = schema.Insert.to_python(params)
        except formencode.Invalid, err:
            return {'status': 400, 'errors': err.unpack_errors()}
        else:
            # we get or create against key but first we have to
            # validate to make sure that key is OK
            exists = model.Repository.view(
                'repository/repo_branch_path',
                key=[
                    self.owner, 
                    self.name, 
                    params['branch'], 
                    params['path']
                ]
            ).first()
            if not exists:
                return {
                    'status': 400, 
                    'errors': {
                        'path': 'this path on this branch of this repo does not exist'
                    }
                }
            else: 
                blob = model.Blob.get_or_create_from(
                    params['repo'],
                    params['branch'],
                    params['path']
                )
                try:
                    blobs = self.document.blobs
                    blobs.insert(params['index'], blob.id)
                    self.document.blobs = blobs
                except IndexError:
                    return {'status': 400, 'errors': {'index': 'Out of range'}}
                else:
                    github = clients.github_factory(user=self.current_user)
                    data = blob.get_data(github)
                    self.document.save()
                    return {
                        'status': 200, 
                        'id': blob.id, 
                        'data': data
                    }
                
            
        
    
    
    @restricted
    def post(self, owner, name, slug):
        self.owner = owner
        self.name = name
        self.slug = slug
        if self.document:
            data = self.insert()
            self.response.status = data.pop('status')
            return data
        else:
            return self.error(404)
        
        
    
    
    def get(self, *args):
        return self.error(405)
        
    
    

class ListenForUpdates(Document):
    """Waits for news from redis.
    """
    
    def listen(self):
        k = self.current_user.id
        t = config.listen_timeout
        
        repo_path = '%s/%s' % (self.owner, self.name)
        redis = Redis(namespace=repo_path)
        
        logging.debug('blocking waiting for %s' % k)
        
        response = redis('blpop', [k], timeout=t)
        
        if response is None:
            return {'status': '304'}
        
        commit_id = response[1]
        data = utils.json_decode(redis[commit_id])
        data.update({'status': 200})
        return data
        
    
    
    @restricted
    def post(self, owner, name, slug):
        self.owner = owner
        self.name = name
        self.slug = slug
        if self.document:
            data = self.listen()
            self.response.status = data.pop('status')
            return data
        else:
            return self.error(404)
        
    
    

class PostCommitHook(RequestHandler):
    """Posted to when a user pushes to github.
    """
    
    def post(self):
        """We get a payload like this::
          
              {
                "after": "0df48053b961ad6f26956ea4bbcbe27c97b7a21b", 
                "before": "ad9aeac5f80097660619349f5dd93fb07a2b2eb0", 
                "commits": [
                  {
                    "added": [], 
                    "author": {
                      "email": "thruflo@googlemail.com", 
                      "name": "James Arthur"
                    }, 
                    "id": "0df48053b961ad6f26956ea4bbcbe27c97b7a21b", 
                    "message": "blah", 
                    "modified": [
                      "README.md"
                    ], 
                    "removed": [], 
                    "timestamp": "2010-05-18T04:13:47-07:00", 
                    "url": "http:\/\/github.com\/thruflo\/Dummy-Bus-Dev\/commit\/0df48053b961ad6f26956ea4bbcbe27c97b7a21b"
                  }
                ], 
                "ref": "refs\/heads\/master", 
                "repository": {
                  "description": "Dummy user account to test github API", 
                  "fork": false, 
                  "forks": 0, 
                  "has_downloads": false, 
                  "has_issues": false, 
                  "has_wiki": false, 
                  "homepage": "http:\/\/dummy.thruflo.com", 
                  "name": "Dummy-Bus-Dev", 
                  "open_issues": 0, 
                  "owner": {
                    "email": "thruflo@googlemail.com", 
                    "name": "thruflo"
                  }, 
                  "private": false, 
                  "url": "http:\/\/github.com\/thruflo\/Dummy-Bus-Dev", 
                  "watchers": 1
                }
              }
          
          We validate it by checking the commit ids against either
          the latest or the handled commits for that branch.
        """
        
        logging.debug('PostCommitHook')
        
        # get the payload
        payload = self.get_argument('payload')
        logging.debug('payload')
        logging.debug(payload)
        data = utils.json_decode(payload)
        
        logging.debug('data')
        logging.debug(data)
        
        # get a handle on the repository
        repo = data['repository']
        branch = data["ref"].split('/')[-1]
        path = '%s/%s' % (repo['owner']['name'], repo['name'])
        docid = model.Repository.get_id_from(path)
        
        # is this actually a repo we have stored?
        repository = model.Repository.get(docid)
        if repository is None:
            return ''
        
        logging.debug('repository')
        logging.debug(repository)
        
        # to validate, either the before matches the latest
        # sanity checked commit, or the latest handled commit
        latest = repository.latest_sanity_checked_commits[branch]
        handled = repository.handled_commits[branch]
        if data['before'] == latest:
            logging.debug('before matched latest commit')
        elif data['before'] in handled:
            logging.debug('before matched one a handled commit')
        else:
            return ''
        
        logging.debug('trying to fetch an authenticated user')
        
        users = repository.users
        users.reverse()
        for user in users:
            github = clients.github_factory(user=user)
            try:
                github.users.make_request('show')
            except RuntimeError:
                github = None
                logging.warning('@@ cache that this user failed to authenticate')
            else:
                break
        
        logging.debug('github')
        logging.debug(github)
        
        if github is not None:
            
            logging.debug('handling commits')
            
            relevant_commits = repository.handle_commits(
                github,
                branch,
                data['commits'],
                before=data['before']
            )
            
            logging.debug('relevant commits')
            logging.debug(relevant_commits)
            
            if relevant_commits:
                # save the repo
                repository.save()
                # augment the data with a list of invalid blob ids
                invalid_blobs = []
                for item in relevant_commits:
                    for k in 'removed', 'modified':
                        for filepath in item.get(k):
                            blob_id = model.Blob.get_id_from(
                                repository.path, 
                                branch, 
                                filepath
                            )
                            invalid_blobs.append(blob_id)
                invalid_blobs = list(set(invalid_blobs))
                # notify any live users
                redis = Redis(namespace=repository.path)
                k = data['after']
                v = {
                    'branch': branch,
                    'invalid_blobs': invalid_blobs,
                    'commits': relevant_commits
                }
                redis[k] = utils.json_encode(v)
                for user in repository.users:
                    redis('rpush', user.id, k)
            
        return ''
        
    
    

