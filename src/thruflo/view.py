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

import clients
import config
import model
import schema
import web
import utils

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
    def wrapper(self, *args, **kwargs):
        redirect_url = _get_redirect_url(self)
        if redirect_url is not None:
            if self.request.method == "GET":
                return self.redirect(redirect_url)
            return self.error(403)
        else:
            repo = self.repository
            if not bool(repo and repo in self.current_user.repositories):
                return self.error(403)
        return method(self, *args, **kwargs)
        
    
    return wrapper
    


class RequestHandler(web.RequestHandler):
    """Provides self.request, default implementations for ``self.account``
      and ``self.current_user``, ``self.redirect()`` and 
      ``self.redirect_to_dashboard()``.
    """
    
    def get_argument(self, name, default=None, strip=True):
        """Returns the value of the argument with the given name.
        """
        
        value = self.request.params.get(name, None)
        if value is None:
            return default
        if strip: value = value.strip()
        return value
        
    
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        logging.debug('user_id: %s' % user_id)
        if user_id:
            user = model.User.get(user_id)
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
    
    @subscribed
    def get(self):
        return self.render_template('dashboard.tmpl')
        
    
    




class SluggedBaseHandler(RequestHandler):
    """Abstract class that handles adding, editing and archiving
      ``model.SluggedDocuments``s.
    """
    
    # a ``model.Container`` impl, e.g.: ``model.Project``
    document_type = NotImplemented 
    
    params = NotImplemented
    schema = NotImplemented
    
    context = None
    
    @property
    def context_type(self):
        if not hasattr(self, '_context_type'):
            self._context_type = self.document_type._doc_type.lower()
        return self._context_type
        
    
    @property
    def context_title(self):
        if not hasattr(self, '_context_title'):
            self._context_title = self.context_type.title()
        return self._context_title
        
    
    
    @property
    def contexts(self):
        if not hasattr(self, '_contexts'):
            doc_type = self.document_type._doc_type
            self._contexts = self.document_type.view(
                'all/type_slug_mod',
                startkey=[self.account.id, doc_type, None, None],
                endkey=[self.account.id, doc_type, [], []],
                include_docs=True
            ).all()
        return self._contexts
        
    
    
    @property
    def github(self):
        if not hasattr(self, '_github'):
            username = self.current_user.github_username
            token = self.current_user.github_token
            self._github = Github(username=username, api_token=token)
        return self._github
        
    
    
    def add(self):
        """``/{document_type}s/add``
        """
        
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return err.unpack_errors()
        else:
            params['account_id'] = self.account.id
            params['slug'] = self.document_type.get_unique_slug(self.account.id)
            doc = self.document_type(**params)
            doc.save()
            return doc
        
    
    def edit(self):
        """``/{document_type}s/{slug}/edit``
        """
        
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return {'status': 400, 'errors': err.unpack_errors()}
        else:
            self.context.update(**params)
            self.context.save()
            return {'status': 200, 'doc': self.context.to_json()}
        
    
    def archive(self):
        """``/{document_type}s/{slug}/archive``
        """
        
        self.context.archived = True
        self.context.save()
        return {'status': 200, 'doc': self.context.to_json()}
        
    
    
    def _compress_args(self, *args):
        """Convert ``('/3002092', '3002092', '/save', 'save', ...)``
          to ``('3002092', 'save', ...)``
        """
        
        _args = []
        
        for i in range(1, len(args), 2):
            _args.append(args[i])
        
        return tuple(_args)
        
    
    
    @subscribed
    def post(self, *args):
        """Dispatches ``/{document_type}/add`` to ``self.add()`` and
          ``/{document_type}/{slug}/{action}`` to ``self.action()``.
        """
        
        args = self._compress_args(*args)
        
        if args[0] == 'add':
            response = self.add()
            if isinstance(response, self.document_type):
                # success, so redirect to the newly created instance
                return self.redirect(
                    '/%ss/%s' % (
                        self.context_type, 
                        response.slug
                    )
                )
            else: # we got an error dict
                return self.render_template(
                    '%ss.tmpl' % self.context_type, 
                    errors=response
                )
        else:
            slug = args[0]
            self.context = self.document_type.get_from_slug(self.account.id, slug)
            if self.context:
                method = getattr(self, args[1])
                data = method(*args[2:])
            else:
                data = {'status': 404, 'errors': {'context': 'Not found'}}
            self.response.status = data.pop('status')
            return data
        
    
    
    @subscribed
    def get(self, *args):
        args = self._compress_args(*args)
        slug = args[0]
        if slug:
            self.context = self.document_type.get_from_slug(self.account.id, slug)
            if self.context:
                return self.render_template('%s.tmpl' % self.context_type)
            else:
                return self.error(404)
        else:
            return self.render_template('%ss.tmpl' % self.context_type, errors={})
        
    
    


class Repositories(SluggedBaseHandler):
    """Add and edit repositories.
    """
    
    document_type = model.Repository 
    
    params = ['name', 'owner', 'url']
    schema = schema.Repository
    
    @property
    def repositories(self):
        """repos/show/:user"
        """
        
        if not hasattr(self, '_repositories'):
            
            repositories = {
                'selected': [],
                'unselected': []
            }
            
            existing_repos = self.contexts
            existing_repo_names = [item.name for item in existing_repos]
            
            username = self.current_user.github_username
            all_repos = self.github.repos.list(username)
            
            for item in all_repos:
                if item.name in existing_repo_names:
                    repositories['selected'].append(item)
                else:
                    repositories['unselected'].append(item)
                
            self._repositories = repositories
        
        return self._repositories
        
    
    
    def select(self):
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return {'status': 400, 'errors': err.unpack_errors()}
        else:
            username = self.current_user.github_username
            doc = model.Repository.view(
                'repository/owner_name',
                key=[self.account.id, username, params['name']],
                include_docs=True
            ).first()
            if not doc:
                params['account_id'] = self.account.id
                doc = model.Repository(**params)
            branches = doc.update_branches(self.github)
            for branch in branches:
                doc.update_blobs(self.github, branch)
            
            doc.save()
            return {'status': 200, 'doc': doc.to_json()}
        
    
    def unselect(self):
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return {'status': 400, 'errors': err.unpack_errors()}
        else:
            username = self.current_user.github_username
            docs = model.Repository.view(
                'repository/owner_name',
                key=[self.account.id, username, params['name']],
                include_docs=True
            ).all()
            try:
                model.Repository.get_db().bulk_delete([doc.to_json() for doc in docs])
            except BulkSaveError, err:
                return {'status': 400, 'errors': err.errors}
            else:
                return {'status': 200}
            
        
    
    
    @subscribed
    def post(self, *args):
        """Exposes ``select`` and ``unselect``.
        """
        
        args_ = self._compress_args(*args)
        if args_[0] in ['select', 'unselect']:
            method = getattr(self, args_[0])
            data = method()
            self.response.status = data.pop('status')
            return data
        else:
            return super(Repositories, self).post(*args)
        
    
    

class Documents(SluggedBaseHandler):
    """Add and edit documents.
    """
    
    document_type = model.Document 
    
    params = ['display_name']
    schema = schema.AddOrEditDocument
    
    @property
    def repositories(self):
        if not hasattr(self, '_repositories'):
            self._repositories = model.Repository.view(
                'all/type_slug_mod',
                startkey=[self.account.id, 'Repository', None, None],
                endkey=[self.account.id, 'Repository', [], []],
                include_docs=True
            ).all()
            logging.warning(
                '@@ need to cache repository commit checking properly'
            )
            force = self.get_argument('force_refresh', False) 
            for item in self._repositories:
                k = '-'.join([item.owner, item.name])
                if force or not self.get_secure_cookie(k):
                    logging.info(
                        '@@ repo commit sanity checking triggered in \
                        ``view.Document.repositories``'
                    )
                    for branch in item.branches:
                        item.update_commits(self.current_user, branch)
                    item.save()
                    self.set_secure_cookie(k, 'cached', expires_days=None)
        return self._repositories
        
    
    
    def insert(self):
        """Get or create a ``Blob``.  Save its position in
          ``self.context.blobs`` and return ``blob.get_data()``.
        """
        
        params = {
            'repo': self.get_argument('repo', None),
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
            owner, name = params['repo'].split('/')
            exists = model.Repository.view(
                'repository/repo_branch_path',
                key=[owner, name, params['branch'], params['path']]
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
                    blobs = self.context.blobs
                    blobs.insert(params['index'], blob.id)
                    self.context.blobs = blobs
                except IndexError:
                    return {'status': 400, 'errors': {'index': 'Out of range'}}
                else:
                    self.context.save()
                    return {
                        'status': 200, 
                        'id': blob.id, 
                        'data': blob.get_data(self.github)
                    }
                
            
        
        
    
    
    def listen(self):
        """Waits for news from redis.
        """
        
        gevent.sleep(50)
        
        return {'status': '304'}
        
        # raise NotImplementedError
        
    
    


class PostCommitHook(RequestHandler):
    """Posted to when a user pushes to github.
    """
    
    def post(self, token):
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
          
          
        """
        
        logging.info('***')
        logging.info(token)
        
        try: # make sure token is a 32 char hash
            token = schema.CouchDocumentId.to_python(token)
        except formencode.Invalid, err:
            logging.warning('Invalid token: %s' % token)
            return ''
        
        logging.info(self.get_argument('payload'))
        
        # get the payload
        data = utils.json_decode(self.get_argument('payload'))
        repo = data['repository']
        
        # have we got a corresponding user?
        user = model.db.query(model.User).filter_by(
            github_username=repo['owner']['name']
        ).first()
        if not user:
            logging.info('not a user')
            return ''
        elif user.github_token != token:
            logging.info('token doesnt match')
            return ''
        
        # is this actually a repo we have stored?
        key = [repo['owner']['name'], repo['name']]
        repos = model.Repository.view(
            'repository/global_owner_name',
            key=key,
            include_docs=True
        ).all()
        if len(repos) > 1:
            logging.warning('@@ race conditions on repo: %s/%s' % (key[0], key[1]))
            for item in repos[:-1]:
                item.delete()
        elif len(repos) == 0:
            logging.info('no repos')
            return ''
        
        doc = repos[-1]
        branch = data["ref"].split('/')[-1]
        
        # handle the commit
        doc.handle_commits(
            user, 
            branch, 
            data['commits'],
            before=data['before']
        )
        doc.save()
        return ''
        
    
    

