#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers for the human web interface.
"""

import logging
import time

from datetime import datetime, timedelta
from operator import itemgetter
from os.path import dirname, join as join_path
from urllib import quote

from tornado import web

from tmpl import render_tmpl
# from utils import json_encode, json_decode

__all__ = [
    'Index', 'Login', 'NotFound'
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
        self.finish(render_tmpl(tmpl_name), **kwargs)
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        self.render_tmpl('index.tmpl')
        
    
    


class Login(RequestHandler):
    """
    """
    
    def get(self):
        raise NotImplementedError
    
    


class NotFound(web.RequestHandler):
    """
    """
    
    def get(self, *args):
        self.render_tmpl('404.tmpl')
        
    
    


