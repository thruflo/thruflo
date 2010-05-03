#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers for the human web interface.
"""

import functools
import logging
import time

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

import formencode
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from tornado import web

import model, schema
from tmpl import render_tmpl
from utils import unicode_urlencode, json_encode, json_decode, get_timezones

__all__ = [
    'Index', 'Login', 'Logout', 'Register', 'Dashboard', 
    'AccountIndex', 'NotFound'
]

class RequestHandler(web.RequestHandler):
    """Base RequestHandler that:
      
      #. gets ``self.current_user`` from a secure cookie
      #. provides ``self.render_tmpl(tmpl_name, **kwargs)`` method
         using mako templates
      
      @@: ``get_current_user`` makes a request to the db for every
          authenticated request
      @@: ``get_account`` does the same for ``@members_only`` and
          ``@admins_only`` requests
      
    """
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        if user_id:
            return model.db.query(model.User).get(int(user_id))
        return None
        
    
    
    @property
    def account(self):
        """Throws an ``AttributeError`` if ``get_account`` hasn't 
          been called
        """
        
        return self._account
        
    
    def get_account(self, account_slug):
        if not getattr(self, '_account', None):
            query = model.db.query(model.Account)
            self._account = query.filter_by(slug=account_slug).first()
        return self._account
        
    
    
    def render_tmpl(self, tmpl_name, **kwargs):
        params = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            reverse_url=self.application.reverse_url
        )
        kwargs.update(params)
        self.finish(render_tmpl(tmpl_name, **kwargs))
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self, *args):
        self.render_tmpl('index.tmpl')
        
    
    


class Login(RequestHandler):
    """Accepts either a username or an email address.
      
      If authenticated, sets the user.id in a secure cookie.
    """
    
    def post(self, *args):
        login = self.get_argument('login', None)
        params = {
            'username': login, 
            'email_address': login,
            'password': self.get_argument('password', None)
        }
        logging.info(params)
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
                self.render_tmpl('login.tmpl', errors=d)
            else:
                p = d.has_key('username') and 'email_address' or 'username'
                kwargs = {}
                kwargs[p] = params['username']
                user = model.db.query(model.User).filter_by(**kwargs).first()
                if user:
                    self.set_secure_cookie(
                        'user_id', 
                        str(user.id),
                        domain='.thruflo.com'
                    )
                    # if we're not on an account page, redirect to
                    # the user's first account
                    path = self.get_argument('next', u'/dashboard')
                    if len(args) and self.get_account(args[0]):
                        pass
                    else:
                        accounts = user.accounts
                        if len(accounts):
                            account_slug = accounts[0].slug
                            path = u'http://%s.thruflo.com%s' % (
                                account_slug,
                                path
                            )
                    self.redirect(path)
                else:
                    self.render_tmpl('login.tmpl', errors={})
                
            
        
    
    
    def get(self, *args):
        self.render_tmpl('login.tmpl', errors={})
        
    
    

class Logout(RequestHandler):
    """
    """
    
    def get(self, *args):
        self.clear_cookie('user_id', domain='.thruflo.com')
        self.redirect(self.get_argument('next', '/'))
        
    
    

class Register(RequestHandler):
    """If we get valid form input, we create a user, store their 
      user.id in a secure cookie and redirect to their dashboard.
    """
    
    @property
    def timezones(self):
        return get_timezones()
    
    
    def post(self, *args):
        params = {
            'username': self.get_argument('username', None),
            'password': self.get_argument('password', None),
            'confirm': self.get_argument('confirm', None),
            'email_address': self.get_argument('email_address', None),
            'first_name': self.get_argument('first_name', None),
            'last_name': self.get_argument('last_name', None),
            'company': self.get_argument('company', None),
            'time_zone': self.get_argument('time_zone', None),
            'account': self.get_argument('account', None)
        }
        logging.info(params)
        try:
            params = schema.Registration.to_python(params)
        except formencode.Invalid, err:
            self.render_tmpl('register.tmpl', errors=err.error_dict)
        else:
            slug = params['account']
            account = model.Account(slug)
            model.db.add(account)
            logging.warning('@@ not bothering with email confirmation yet')
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
                self.render_tmpl('register.tmpl', errors=errors)
            else:
                self.set_secure_cookie(
                    'user_id', 
                    str(user.id),
                    domain='.thruflo.com'
                )
                self.redirect(self.get_argument('next', u'/dashboard'))
            
        
        
    
    
    def get(self, *args):
        self.render_tmpl('register.tmpl', errors={})
        
    
    


def members_only(method):
    """Users accessing methods decorated with ``@members_only``
      must be members of the current account.
    """
    
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        authorised = False
        if self.current_user:
            account = self.get_account(args[0])
            if account in self.current_user.accounts:
                authorised = True
        if not authorised:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + unicode_urlencode(
                        dict(next=self.request.uri)
                    )
                self.redirect(url)
                return
            raise web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
    
    


class Dashboard(RequestHandler):
    """
    """
    
    @members_only
    def get(self, account_slug):
        self.render_tmpl('dashboard.tmpl')
    
    


class AccountIndex(RequestHandler):
    """Landing on ``/:account/`` redirects to ``/:account/dashboard``
      if the ``Account`` exists.
    """
    
    def get(self, *args):
        account = self.get_account(args[0])
        if account:
            self.redirect('/dashboard')
        else:
            self.render_tmpl('404.tmpl')
        
    
    

class NotFound(RequestHandler):
    """
    """
    
    def get(self, *args):
        self.render_tmpl('404.tmpl')
        
    
    


