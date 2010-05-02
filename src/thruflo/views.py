#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers for the human web interface.
"""

import logging
import time

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import quote

from tornado import web

from model import *
from tmpl import render_tmpl
from utils import json_encode, json_decode

__all__ = [
    'Index', 'Login', 'Register', 'NotFound'
]

class RequestHandler(web.RequestHandler):
    """Base RequestHandler that:
      
      #. gets ``self.current_user`` from a secure cookie
      #. provides ``self.render_tmpl(tmpl_name, **kwargs)`` method
         using mako templates
      
      @@: ``get_current_user`` makes a request to the db for every
          authenticated request
    """
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        return user_id and User.get(user_id) or None
        
    
    
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
    
    def get(self):
        self.render_tmpl('index.tmpl')
        
    
    


class Login(RequestHandler):
    """
    """
    
    def post(self, *args):
        errors = {}
        
        logging.info('@@')
        
        login = self.get_argument('login', None)
        password = self.get_argument('password', None)
        
        logging.info(login)
        logging.info(password)
        
        if not login:
            errors['login'] = u'Please enter a username or email address'
        else:
            try:
                SlugProperty().validate(login)
            except ValueError:
                try:
                    EmailProperty().validate(login)
                except ValueError:
                    errors['login'] = u'%s is not a valid username or email address'
        if not password:
            errors['password'] = u'Please enter a password'
        else:
            try:
                password = PasswordProperty().validate(password)
            except ValueError, err:
                errors['password'] = unicode(err)
        if errors:
            self.render_tmpl('login.tmpl', errors=errors)
        else:
            logging.warning('@@ not bothering with email confirmation yet')
            user = User.view(
                'users/authenticate', 
                key=[login, password]
            ).one()
            if user:
                self.set_secure_cookie('user_id', unicode(user._id))
                self.redirect(u'/%s/dashboard' % username)
            else:
                self.render_tmpl('login.tmpl', errors={})
            
        
    
    
    def get(self):
        self.post()
        # self.render_tmpl('login.tmpl', errors={})
        
    
    


class Register(RequestHandler):
    """If we get valid form input, we create a user,
      store their doc._id in a secure cookie and
      redirect to their dashboard.
    """
    
    def post(self):
        errors = {}
        
        username = self.get_argument('username', None)
        email = self.get_argument('email', None)
        password = self.get_argument('password', None)
        confirm = self.get_argument('confirm', None)
        
        if not username:
            errors['username'] = u'Please choose a username'
        else:
            try:
                SlugProperty().validate(username)
            except ValueError, err:
                errors['username'] = u'%s is not a valid username'
            else:
                exists = User.view(
                    'users/authenticate', 
                    startkey=[username, False],
                    endkey=[username, u'\u9999']
                ).count()
                if exists:
                    errors['username'] = u'%s is already taken'
        if not email:
            errors['email'] = u'Please enter your email address'
        else:
            try:
                EmailProperty().validate(email)
            except ValueError, err:
                errors['username'] = unicode(err)
            else:
                exists = User.view(
                    'users/authenticate', 
                    startkey=[email, False],
                    endkey=[email, u'\u9999']
                ).count()
                if exists:
                    errors['email'] = u'%s is already taken'
        if not password:
            errors['password'] = u'Please choose a password'
        else:
            try:
                PasswordProperty().validate(password)
            except ValueError, err:
                errors['password'] = unicode(err)
            else:
                if not confirm:
                    errors['confirm'] = u'Please confirm your password'
                else:
                    if confirm != password:
                        msg = u'Password and confirm password don\'t match'
                        errors['password'] = msg
                        errors['confirm'] = msg
        if errors:
            self.render_tmpl('register.tmpl', errors=errors)
        else:
            logging.warning('@@ register hardcodes an account')
            logging.warning('@@ not taking any steps to handle race condition uniqueness edge case')
            logging.warning('@@ not bothering with email confirmation yet')
            user = User(
                username=username,
                password=password,
                email_address = email,
                confirmation_hash = generate_hash(),
                administrator_accounts = [username]
            )
            user.save()
            self.set_secure_cookie('user_id', unicode(user._id))
            self.redirect(u'/%s/dashboard' % username)
            
        
    
    
    def get(self):
        self.render_tmpl('register.tmpl', errors={})
        
    
    


class NotFound(RequestHandler):
    """
    """
    
    def get(self, *args):
        self.render_tmpl('404.tmpl')
        
    
    


