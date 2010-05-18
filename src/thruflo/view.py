#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers.
"""

import functools
import sys
import time
import urllib2

import logging

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

import formencode
import webob

from sqlalchemy.exc import IntegrityError, InvalidRequestError

import model
import schema
import template
import web
import utils
import urllib2

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
            if default is None:
                raise self.error(404, "Missing argument %s" % name)
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
            return self.render_template('register.tmpl', errors=err.error_dict)
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
                startkey=[self.account.id, doc_type, False, False],
                endkey=[self.account.id, doc_type, [], []],
                include_docs=True
            ).all()
        return self._contexts
        
    
    
    def add(self):
        """``/{document_type}s/add``
        """
        
        params = {}
        for item in self.params:
            params[item] = self.get_argument(item, None)
        try:
            params = self.schema.to_python(params)
        except formencode.Invalid, err:
            return err.error_dict
        else:
            params['account_id'] = self.account.id
            params['slug'] = self.container_type.get_unique_slug(self.account.id)
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
            return {'status': 500, 'errors': err.error_dict}
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
                    errors=error_dict
                )
        else:
            slug = args[0]
            self.context = self.container_type.get_from_slug(self.account.id, slug)
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
            self.context = self.container_type.get_from_slug(self.account.id, slug)
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
    

class Documents(SluggedBaseHandler):
    """Add and edit documents.
    """
    
    document_type = model.Document 
    
    params = ['sources', 'stylesheet', 'content']
    schema = schema.Document

class Stylesheets(SluggedBaseHandler):
    """Add and edit stylesheets.
    """
    
    document_type = model.Stylesheet 
    
    params = ['source', 'content']
    schema = schema.Stylesheet
    

