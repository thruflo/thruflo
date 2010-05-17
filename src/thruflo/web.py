#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simplified version of `Tornado <http://www.tornadoweb.org/>`_s 
  ``web.RequestHandler``.
"""

import base64
import binascii
import calendar
import Cookie
import datetime
import email.utils
import escape
import hashlib
import hmac
import httplib
import logging
import os.path
import re
import time
import urlparse
import uuid

import webob

import config
import template
import utils

class BaseRequestHandler(object):
    """Provides ``self.settings``, ``self.current_user``, ``self.account``, 
      secure cookies, ``static_url()`` and ``xsrf_form_html()``.
    """
    
    response = webob.Response(
        status=200, 
        content_type='text/html; charset=UTF-8'
    )
    
    @property
    def settings(self):
        return config.settings
        
    
    
    @property
    def cookies(self):
        """A dictionary of Cookie.Morsel objects.
        """
        
        return self.request.cookies
        
    
    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default.
        """
        
        return self.request.cookies.get(name, default)
        
    
    def set_cookie(
            self, 
            name, 
            value, 
            domain=None, 
            expires=None, 
            path="/", 
            expires_days=None, 
            override=False
        ):
        """Sets the given cookie name/value with the given options.
        """
        
        name = _utf8(name)
        value = _utf8(value)
        
        if re.search(r"[\x00-\x20]", name + value):
            # Don't let us accidentally inject bad stuff
            raise ValueError("Invalid cookie %r: %r" % (name, value))
        
        max_age = None
        if expires_days:
            max_age = expires_days * 24 * 60 * 60
        
        if override:
            self.response.unset_cookie(name, strict=False)
        
        self.response.set_cookie(
            name, 
            value=value,
            path=path, 
            domain=domain, 
            expires=expires, 
            max_age=max_age
        )
        
    
    def clear_cookie(self, name, path="/", domain=None):
        """Deletes the cookie with the given name.
        """
        
        self.response.set_cookie(
            name, 
            '', 
            path=path, 
            domain=domain, 
            max_age=0, 
            expires=datetime.timedelta(days=-5)
        )
        
    
    
    def _cookie_signature(self, *parts):
        h = hmac.new(self.settings["cookie_secret"], digestmod=hashlib.sha1)
        for part in parts: h.update(part)
        return h.hexdigest()
        
    
    def set_secure_cookie(self, name, value, expires_days=30, **kwargs):
        """Signs and timestamps a cookie so it cannot be forged.
        
        You must specify the 'cookie_secret' setting in your Application
        to use this method. It should be a long, random sequence of bytes
        to be used as the HMAC secret for the signature.
        
        To read a cookie set with this method, use get_secure_cookie().
        """
        
        timestamp = str(int(time.time()))
        value = base64.b64encode(value)
        signature = self._cookie_signature(name, value, timestamp)
        value = "|".join([value, timestamp, signature])
        self.set_cookie(
            name,
            value, 
            expires_days=expires_days, 
            **kwargs
        )
        
    
    def get_secure_cookie(self, name, include_name=True, value=None):
        """Returns the given signed cookie if it validates, or None.
        """
        
        if value is None: value = self.get_cookie(name)
        if not value: return None
        parts = value.split("|")
        if len(parts) != 3: return None
        if include_name:
            signature = self._cookie_signature(name, parts[0], parts[1])
        else:
            signature = self._cookie_signature(parts[0], parts[1])
        if not _time_independent_equals(parts[2], signature):
            logging.warning("Invalid cookie signature %r", value)
            return None
        timestamp = int(parts[1])
        if timestamp < time.time() - 31 * 86400:
            logging.warning("Expired cookie %r", value)
            return None
        try:
            return base64.b64decode(parts[0])
        except:
            return None
        
        
    
    
    def _compress_args(self, *args):
        """Convert ``('/3002092', '3002092', '/save', 'save', ...)``
          to ``('3002092', 'save', ...)``
        """
        
        _args = []
        for i in range(1, len(args), 2):
            _args.append(args[i])
        return tuple(_args)
        
    
    
    @property
    def current_user(self):
        """The authenticated user for this request.
        """
        
        if not hasattr(self, "_current_user"):
            self._current_user = self.get_current_user()
        return self._current_user
        
    
    def get_current_user(self):
        """Override to determine the current user from, e.g., a cookie.
        """
        
        return None
        
    
    
    @property
    def account(self):
        if not hasattr(self, "_account"):
            self._account = self.get_account()
        return self._account
        
    
    def get_account(self):
        """Override to determine the current account.
        """
        
        return None
        
    
    
    @property
    def xsrf_token(self):
        """The XSRF-prevention token for the current user/session.
        """
        
        if not hasattr(self, "_xsrf_token"):
            token = self.get_cookie("_xsrf")
            if not token:
                token = binascii.b2a_hex(uuid.uuid4().bytes)
                expires_days = 30 if self.current_user else None
                self.set_cookie("_xsrf", token, expires_days=expires_days)
            self._xsrf_token = token
        return self._xsrf_token
        
    
    def check_xsrf_cookie(self):
        """Verifies that the '_xsrf' cookie matches the '_xsrf' argument.
        """
        
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return
        
        token = self.get_argument("_xsrf", None)
        if not token:
            raise HTTPError(403, "'_xsrf' argument missing from POST")
        if self.xsrf_token != token:
            raise HTTPError(403, "XSRF cookie does not match POST argument")
        
    
    
    def xsrf_form_html(self):
        """An HTML <input/> element to be included with all POST forms.
        """
        
        v = escape.xhtml_escape(self.xsrf_token)
        return '<input type="hidden" name="_xsrf" value="%s"/>' % v
        
    
    def static_url(self, path):
        """Returns a static URL for the given relative static file path.
        """
        
        if not hasattr(BaseRequestHandler, "_static_hashes"):
            BaseRequestHandler._static_hashes = {}
        hashes = BaseRequestHandler._static_hashes
        if path not in hashes:
            file_path = os.path.join(self.settings["static_path"], path)
            try:
                f = open(file_path)
            except IOError:
                logging.error("Could not open static file %r", path)
                hashes[path] = None
            else:
                hashes[path] = hashlib.md5(f.read()).hexdigest()
                f.close()
        base = self.request.host_url
        static_url_prefix = self.settings.get('static_url_prefix', '/static/')
        if hashes.get(path):
            return base + static_url_prefix + path + "?v=" + hashes[path][:5]
        else:
            return base + static_url_prefix + path
        
    
    
    def render_template(self, tmpl_name, **kwargs):
        params = dict(
            handler=self,
            request=self.request,
            account=self.account,
            current_user=self.current_user,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html
        )
        kwargs.update(params)
        return template.render_tmpl(tmpl_name, **kwargs)
        
    
    
    def redirect(self, url, status=302, content_type=None):
        """Handle redirecting.
        """
        
        self.response.status = status
        if not self.response.headerlist:
            self.response.headerlist = []
        self.response.headerlist.append(('Location', url))
        if content_type:
            self.response.content_type = content_type
        return self.response
        
    
    def respond_with(self, what, status=200, content_type=None):
        """Augment self.response and return it.
        """
        
        if status:
            self.response.status = status
        if content_type:
            self.response.content_type = content_type
        
        if isinstance(what, str):
            self.response.body = what
        elif isinstance(what, unicode):
            self.response.unicode_body = what
        else: # assume it's data
            self.response.content_type = 'application/json; charset=UTF-8'
            self.response.unicode_body = utils.json_encode(what)
        
        return self.response
        
    


def _utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    assert isinstance(s, str)
    return s
    

def _unicode(s):
    if isinstance(s, str):
        try:
            return s.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Non-utf8 argument")
    assert isinstance(s, unicode)
    return s
    

def _time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
    

