#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers.
"""

import functools
import logging

from datetime import datetime, timedelta

import formencode

from webapp import web, utils

import model
import schema

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
        """
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
        """
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
            """
            repo_path = '%s/%s' % (repo_owner, repo_name)
            if not bool(repo_path in self.current_user.repositories):
                return self.error(403)
            """
        return method(self, repo_owner, repo_name, *args, **kwargs)
        
    
    return wrapper
    


class RequestHandler(web.RequestHandler):
    """Implements ``self.get_current_user()``.
    """
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        logging.debug('user_id: %s' % user_id)
        if user_id:
            user = model.User.soft_get(user_id)
            logging.debug('user: %s' % user)
            return user
        return None
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        if self.current_user:
            self.redirect('/dashboard')
        else:
            self.render_tmpl('index.tmpl')
        
        
    
    

class Login(RequestHandler):
    """If authenticated, sets the user.id in a secure cookie.
    """
    
    def post(self):
        params = {
            'username': self.get_argument('username', None), 
            'password': self.get_argument('password', None)
        }
        try:
            params = schema.Login.to_python(params)
        except formencode.Invalid, err:
            self.render_tmpl('login.tmpl', errors=err.error_dict)
        else:
            user = model.User.authenticate(
                params['username'], 
                params['password']
            )
            if user:
                self.set_secure_cookie(
                    'user_id', 
                    str(user.id),
                    domain='.%s' % self.settings['domain']
                )
                self.redirect('/dashboard')
            else:
                self.render_tmpl('login.tmpl', errors={})
            
        
        
    
    
    def get(self):
        self.render_tmpl('login.tmpl', errors={})
        
    
    

class Logout(RequestHandler):
    """
    """
    
    def get(self):
        self.clear_cookie(
            'user_id', 
            domain='.%s' % self.settings['domain']
        )
        self.redirect(
            self.get_argument('next', '/')
        )
        
    
    

class Register(RequestHandler):
    """If we get valid form input, we create a ``Repository``,
      with the username as owner
      user.id in a secure cookie and redirect to their dashboard.
    """
    
    def post(self):
        params = {
            'username': self.get_argument('username', None),
            'password': self.get_argument('password', None),
            'confirm': self.get_argument('confirm', None),
            'email_address': self.get_argument('email_address', None),
            'name': self.get_argument('name', None)
        }
        try:
            params = schema.Register.to_python(params)
        except formencode.Invalid, err:
            self.render_tmpl('register.tmpl', errors=err.error_dict)
        else:
            username = params['username']
            # create repo
            slug = model.Repository.get_unique_slug(namespace=username)
            repo = model.Repository(slug=slug)
            repo.save()
            # create user
            params['owned'] = [repo.id]
            user = model.User.create_user(
                username, 
                params
            )
            if not user:
                errors = {'username': '%s already taken.'}
                self.render_tmpl('register.tmpl', errors=errors)
            else:
                self.set_secure_cookie(
                    'user_id', 
                    str(user.id),
                    domain='.%s' % self.settings['domain']
                )
                self.redirect('/dashboard')
                
            
        
        
    
    
    def get(self):
        self.render_tmpl('register.tmpl', errors={})
        
    
    

class Dashboard(RequestHandler):
    """
    """
    
    @members_only
    def get(self):
        self.render_tmpl('dashboard.tmpl')
        
    
    


