#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers.
"""

import functools
import sys
import time
import urllib2

import logging
if sys.platform=='darwin':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('beaker').setLevel(logging.INFO)
    logging.getLogger('restkit').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('beaker').setLevel(logging.WARNING)
    logging.getLogger('restkit').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

import formencode
import webob

from github2.client import Github

from couchdbkit.exceptions import BulkSaveError
from sqlalchemy.exc import IntegrityError, InvalidRequestError

import config
import model
import schema
import template
import web
import utils

def members_only(method):
    """Users accessing methods decorated with ``@members_only``
      must be members of the current account.
    """
    
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        authorised = False
        if self.current_user:
            account = self.account
            if account and account in self.current_user.accounts:
                authorised = True
        if not authorised:
            if self.request.method == "GET":
                url = self.settings['login_url']
                if "?" not in url:
                    url += "?" + utils.unicode_urlencode(
                        dict(next=self.request.path)
                    )
                self.redirect(url)
                return
            raise self.error(403)
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
        
    
    
    def get_account(self):
        host = unicode(self.request.host)
        parts = host.split(self.settings['domain'])
        account_slug = parts[0]
        if account_slug:
            account_slug = account_slug[:-1]
            query = model.db.query(model.Account)
            return query.filter_by(slug=account_slug).first()
        return None
        
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        logging.debug('user_id: %s' % user_id)
        if user_id:
            user = model.db.query(model.User).get(int(user_id))
            logging.debug('user: %s' % user)
            return user
        return None
        
    
    
    def redirect_to_dashboard(self, user):
        """If we're not on an account page, redirect to 
          the user's first account
        """
        
        
        path = self.get_argument('next', u'/dashboard')
        
        if not self.account:
            accounts = user.accounts
            if len(accounts):
                account_slug = accounts[0].slug
                path = u'http://%s.%s%s' % (
                    account_slug,
                    self.settings['domain'],
                    path
                )
            
        return self.redirect(path)
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        if self.account:
            return self.redirect('/dashboard')
        else:
            return self.render_template('index.tmpl')
        
        
    
    

class Login(RequestHandler):
    """Accepts either a username or an email address. 
      If authenticated, sets the user.id in a secure cookie.
    """
    
    def post(self):
        logging.info('login')
        login = self.get_argument('login', None)
        params = {
            'username': login, 
            'email_address': login,
            'password': self.get_argument('password', None)
        }
        try:
            params = schema.Login.to_python(params)
        except formencode.Invalid, err:
            # were *both* username *and* email_address invalid?
            d = err.error_dict
            if d.has_key('username') and d.has_key('email_address'):
                d.pop('username')
                d.pop('email_address')
                d['login'] = u'Invalid username or email address'
            if d.has_key('password') or d.has_key('login'):
                return self.render_template('login.tmpl', errors=d)
            else:
                p = d.has_key('username') and 'email_address' or 'username'
                kwargs = {}
                kwargs[p] = params['username']
                kwargs['password'] = schema.SecurePassword.to_python(params['password'])
                logging.info(kwargs)
                user = model.db.query(model.User).filter_by(**kwargs).first()
                if user:
                    self.set_secure_cookie(
                        'user_id', 
                        str(user.id),
                        domain='.%s' % self.settings['domain']
                    )
                    return self.redirect_to_dashboard(user)
                else:
                    return self.render_template('login.tmpl', errors={})
                
            
        
    
    def get(self):
        return self.render_template('login.tmpl', errors={})
        
    
    

class Logout(RequestHandler):
    """Clear cookie and redirect.
    """
    
    def get(self):
        domain = '.%s' % self.settings['domain']
        next = self.get_argument('next', '/')
        self.clear_cookie('user_id', domain=domain)
        return self.redirect(next)
        
    
    

class Register(RequestHandler):
    """If we get valid form input, we create a user, store their 
      user.id in a secure cookie and redirect to their dashboard.
    """
    
    @property
    def timezones(self):
        return utils.get_timezones()
        
    
    
    def post(self):
        params = {
            'username': self.get_argument('username', None),
            'password': self.get_argument('password', None),
            'confirm': self.get_argument('confirm', None),
            'email_address': self.get_argument('email_address', None),
            'first_name': self.get_argument('first_name', None),
            'last_name': self.get_argument('last_name', None),
            'github_username': self.get_argument('github_username', None),
            'github_token': self.get_argument('github_token', None),
            'time_zone': self.get_argument('time_zone', None),
            'account': self.get_argument('username', None)
        }
        try:
            params = schema.Registration.to_python(params)
        except formencode.Invalid, err:
            return self.render_template('register.tmpl', errors=err.unpack_errors())
        else:
            slug = params['account']
            account = model.Account(slug)
            model.db.add(account)
            logging.warning('@@ not bothering with email confirmation yet')
            logging.warning('@@ not bothering to check github creds pending oauth...')
            params.pop('account')
            params.pop('confirm')
            user = model.User(
                administrator_accounts = [account],
                **params
            )
            model.db.add(user)
            try:
                model.db.commit()
            except IntegrityError, err:
                model.db.rollback()
                errors = {'message': err.args[0]}
                return self.render_template('register.tmpl', errors=errors)
            else:
                self.set_secure_cookie(
                    'user_id', 
                    str(user.id),
                    domain='.%s' % self.settings['domain']
                )
                return self.redirect_to_dashboard(user)
            
        
    
    def get(self):
        return self.render_template('register.tmpl', errors={})
        
    
    

class Dashboard(RequestHandler):
    """
    """
    
    @members_only
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
        
    
    
    @members_only
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
        
    
    
    @members_only
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
            
        
    
    
    @members_only
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
            for item in self._repositories:
                k = '-'.join([item.owner, item.name])
                if not self.get_secure_cookie(k):
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
                
            
        
        
    
    


class Stylesheets(SluggedBaseHandler):
    """Add and edit stylesheets.
    """
    
    document_type = model.Stylesheet 
    
    params = ['source', 'content']
    schema = schema.Stylesheet
    


class PostCommitHook(web.RequestHandler):
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
        
        logging.info(dir(self.request))
        logging.info(self.request.body)
        
        # get the payload
        data = utils.json_decode(self.request.body)
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
        branch = repo["ref"].split('/')[-1]
        
        # handle the commit
        doc.handle_commits(
            user, 
            branch, 
            data['commits'],
            before=data['before']
        )
        doc.save()
        return ''
        
    
    

