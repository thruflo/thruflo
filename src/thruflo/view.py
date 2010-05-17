#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""`Bobo <http://bobo.digicool.com>`_ web application.
"""

import functools
import sys
import time
import urllib2

import logging
if sys.platform=='darwin':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('beaker.container').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('beaker.container').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)


from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

import bobo
import formencode
import webob

from sqlalchemy.exc import IntegrityError, InvalidRequestError

import model
import schema
import template
import web
import utils

def members_only(self, request, func):
    authorised = False
    if self.current_user:
        account = self.account
        if account and account in self.current_user.accounts:
            authorised = True
    if not authorised:
        if request.method == "GET":
            url = self.settings['login_url']
            if "?" not in url:
                url += "?" + utils.unicode_urlencode(
                    dict(next=self.request.path)
                )
            return self.redirect(url)
        return webob.Response(status=403)
    
    


class RequestHandler(web.BaseRequestHandler):
    """Provides self.request, default implementations for ``self.account``
      and ``self.current_user``, ``self.redirect()`` and 
      ``self.redirect_to_dashboard()``.
    """
    
    def __init__(self, request, *args):
        self.request = request
        self.request.charset = 'utf8'
        
    
    
    def get_argument(self, name, default=None, strip=True):
        """Returns the value of the argument with the given name.
        """
        
        value = self.request.params.get(name, None)
        if value is None:
            if default is None:
                raise bobo.NotFound("Missing argument %s" % name)
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
        
    
    


@bobo.subroute('/', scan=True)
class Index(RequestHandler):
    
    @bobo.query('')
    def index(self):
        if self.account:
            return self.redirect('/dashboard')
        else:
            return self.render_template('index.tmpl')
        
        
    
    


@bobo.subroute('/login', scan=True)
class Login(RequestHandler):
    """Accepts either a username or an email address. 
      If authenticated, sets the user.id in a secure cookie.
    """
    
    @bobo.post('')
    @bobo.post('/')
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
                
            
        
    
    
    @bobo.query('')
    @bobo.query('/')
    def get(self):
        return self.render_template('login.tmpl', errors={})
        
    
    


@bobo.subroute('/logout', scan=True)
class Logout(RequestHandler):
    """Clear cookie and redirect.
    """
    
    @bobo.query('')
    @bobo.query('/')
    def get(self):
        self.clear_cookie(
            'user_id', 
            domain='.%s' % self.settings['domain']
        )
        return self.redirect(
            self.get_argument('next', '/')
        )
        
    
    


@bobo.subroute('/register', scan=True)
class Register(RequestHandler):
    """If we get valid form input, we create a user, store their 
      user.id in a secure cookie and redirect to their dashboard.
    """
    
    @property
    def timezones(self):
        return utils.get_timezones()
        
    
    
    @bobo.post('')
    @bobo.post('/')
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
            
        
    
    
    @bobo.query('')
    @bobo.query('/')
    def get(self):
        return self.render_template('register.tmpl', errors={})
        
    
    


@bobo.subroute('/dashboard', scan=True)
class Dashboard(RequestHandler):
    """
    """
    
    @bobo.query('', check=members_only)
    @bobo.query('/', check=members_only)
    def get(self):
        return self.render_template('dashboard.tmpl')
        
    
    


"""

@bobo.subroute('/repositories', scan=True)
class Repositories(RequestHandler):
    @property
    def repositories(self):
        r = urllib2.Request(
        
        )
        sock = urllib2.urlopen
        http://github.com/api/v2/yaml/repos/show/schacon
        
    
    
    @bobo.query('', check=members_only)
    @bobo.query('/', check=members_only)
    def get(self):
        return self.render_template('repositories.tmpl')
        
    



"""
