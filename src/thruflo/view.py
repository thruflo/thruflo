#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers.
"""

import functools
import logging
import urllib
import urlparse

from datetime import datetime, timedelta

import formencode
import webob

from thruflo.webapp import web, utils
from thruflo.webapp.cache import Redis

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
    """else:
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
    def wrapper(self, *args, **kwargs):
        redirect_url = _get_redirect_url(self)
        if redirect_url is not None:
            if self.request.method == "GET":
                return self.redirect(redirect_url)
            return self.error(403)
        elif not self.repository:
            return self.error(404)
        elif not self.repository.id in self.current_user.repositories:
            return self.error(403)
        return method(self, *args, **kwargs)
        
    
    return wrapper
    


class RequestHandler(web.RequestHandler):
    """Base RequestHandler for this webapp implementation.
    """
    
    def get_current_user(self):
        """Get the current user from a ``user.id`` stored 
          in a secure cookie, or return ``None``.
        """
        
        user_id = self.get_secure_cookie("user_id")
        logging.debug('user_id: %s' % user_id)
        
        if user_id:
            user = model.User.soft_get(user_id)
            logging.debug('user: %s' % user)
            return user
        
        return None
        
    
    def redirect_on_login(self):
        """Redirect to ``/:username/:repo.slug``.
        """
        
        logging.warning('@@ select default repo from last viewed')
        
        user = self.current_user
        repo_id = user.owned[0]
        repo = model.Repository.get(repo_id)
        
        next_url = '/%s/%s' % (user.username, repo.slug)
        return self.redirect(next_url)
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        if self.current_user:
            return self.redirect_on_login()
        else:
            return self.render_template('index.tmpl')
        
        
    
    

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
            self.render_template(
                'login.tmpl', 
                errors=err.error_dict,
                message=None
            )
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
                self._current_user = user
                return self.redirect_on_login()
            else:
                return self.render_template(
                    'login.tmpl', 
                    errors={},
                    message=u'Login unsuccessful.'
                )
            
        
        
    
    
    def get(self):
        return self.render_template(
            'login.tmpl', 
            errors={},
            message=None
        )
        
    
    

class Logout(RequestHandler):
    """
    """
    
    def get(self):
        self.clear_cookie(
            'user_id', 
            domain='.%s' % self.settings['domain']
        )
        return self.redirect(
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
            'email': self.get_argument('email', None),
            'name': self.get_argument('name', None)
        }
        try:
            params = schema.Register.to_python(params)
        except formencode.Invalid, err:
            return self.render_template('register.tmpl', errors=err.error_dict)
        else:
            params.pop('confirm')
            username = params['username']
            # create repo
            slug = model.Repository.get_unique_slug(namespace=username)
            repo = model.Repository(slug=slug, namespace=username)
            repo.save()
            # create user
            params['owned'] = [repo.id]
            user = model.User.create_user(
                username, 
                params
            )
            if not user:
                errors = {'username': '%s already taken.'}
                return self.render_template('register.tmpl', errors=errors)
            else:
                user.save()
                self.set_secure_cookie(
                    'user_id', 
                    str(user.id),
                    domain='.%s' % self.settings['domain']
                )
                self._current_user = user
                return self.redirect_on_login()
                
            
        
        
    
    
    def get(self):
        return self.render_template('register.tmpl', errors={})
        
    
    


class Editor(RequestHandler):
    """
    """
    
    @property
    def repository(self):
        if not hasattr(self, '_repository'):
            repository = None
            parts = self.request.path.split('/')
            if len(parts) > 2:
                try:
                    username = schema.Username.to_python(parts[1])
                    slug = schema.Slug.to_python(parts[2])
                except formencode.Invalid, err:
                    pass
                else:
                    repository = model.Repository.get_from_slug(
                        username,
                        slug
                    )
            self._repository = repository
        return self._repository
        
    
    
    @property
    def documents_list(self):
        """A list of dicts::
          
              [{
                      'value': [
                          '2-1ef8f88931b08ed7842a0cf511575941', # rev
                          '2010-06-26T10:14:22Z'# mod
                      ], 
                      'id': '8c4bd062ec3d096db552ab12471452ac', 
                      'key': [
                          'c18862966c9a294c0f4ed6558a63540b', # repo id
                          'Doc 3' # title
                      ]
                  }
              ]
          
        """
        
        if not hasattr(self, '_documents_list'):
            self._documents_list = self.repository.list_documents()
        return self._documents_list
        
    
    
    def _notify_doc_changed(self, doc):
        """Get all the ``client_id``s that are live against a repo and 
          push the new / changed ``doc._id`` and ``doc.title`` to them.
        """
        
        logging.debug('notify doc changed')
        
        mod = doc.mod.replace(microsecond=0).isoformat() + 'Z'
        data = {'_id': doc.id, 'title': doc.title.encode('utf8'), 'mod': mod}
        
        redis = Redis(namespace=self.repository.id, expire_after=300)
        redis_ready_data = urllib.urlencode(data)
        
        logging.debug(redis_ready_data)
        logging.debug(type(redis_ready_data))
        
        for key in redis('keys', 'client-*'):
            client_id = key.split('client-')[1]
            redis('rpush', client_id, data)
        
        
    
    
    def _overwrite(self):
        """Save overwrites the content of a previously stored
          document.  If the ``doc._rev`` is out of date, this 
          will raise an error.
          
          @@ todo: handle conflicts / merging.
        """
        
        params = {
            '_id': self.get_argument('_id', u''),
            '_rev': self.get_argument('_rev', u''),
            'path': self.get_argument('path', u''),
            'title': self.get_argument('title', u''),
            'content': self.get_argument('content', u'')
        }
        try:
            params = schema.OverwriteDocument.to_python(params)
        except formencode.Invalid, err:
            data = utils.json_encode(err.error_dict)
            return self.error(400, body=data)
        else:
            params['repository'] = self.repository.id
            doc = model.Document(**params)
            doc.save()
            self._notify_doc_changed(doc)
            return {'_id': doc._id, '_rev': doc._rev}
            
        
    
    def _create(self):
        """Creates a new document called ``title`` at ``path``
          with the ``content`` provided.
        """
        
        params = {
            'path': self.get_argument('path'),
            'title': self.get_argument('title'),
            'content': self.get_argument('content')
        }
        try:
            params = schema.CreateDocument.to_python(params)
        except formencode.Invalid, err:
            data = utils.json_encode(err.error_dict)
            return self.error(400, body=data)
        else:
            params['repository'] = self.repository.id
            doc = model.Document(**params)
            doc.save()
            self._notify_doc_changed(doc)
            return {'_id': doc._id, '_rev': doc._rev}
            
        
    
    def _fetch(self):
        _id = self.get_argument('_id', u'')
        try:
            _id = schema.CouchDocumentId(not_empty=True).to_python(_id)
        except formencode.Invalid, err:
            data = utils.json_encode({'_id': 'Invalid ``_id``'})
            return self.error(400, body=data)
        else:
            doc = model.Document.soft_get(_id)
            return {'doc': doc and doc.to_json() or None}
        
    
    
    def _listen(self):
        """Register the ``client_id`` against the repo in redis, so 
          it's renewed every poll and expires after a few minutes.
          
          Listen for updates against it.
        """
        
        client_id = self.get_argument('client_id', u'')
        logging.debug(client_id)
        try:
            client_id = schema.ClientId(not_empty=True).to_python(client_id)
        except formencode.Invalid, err:
            data = utils.json_encode({'_id': 'Invalid ``client_id``'})
            return self.error(400, body=data)
        else:
            redis = Redis(namespace=self.repository.id, expire_after=300)
            timeout = self.settings['listen_timeout']
            # (re)-register the client_id
            client_key = 'client-%s' % client_id
            redis[client_key] = client_id
            # wait for updates
            logging.debug('blocking waiting for %s' % client_id)
            response = redis('blpop', [client_id], timeout=timeout)
            # if it timed out, no worries
            if response is None:
                return webob.Response(status=304)
            # if we got something, return it
            data = eval(response[1])
            for item in data:
                data[item] = data[item].decode('utf8')
            logging.debug(data)
            return data
        
        
    
    
    @restricted
    def post(self, action):
        """Acts as a little dispatch script to send
          actions to the corresponding method.
          
          (The action is validated by the url mapping).
        """
        
        return getattr(self, '_%s' % action)()
        
    
    
    @restricted
    def get(self):
        return self.render_template('editor.tmpl')
        
    
    

class Bespin(RequestHandler):
    """Just serves the static bespin page.  It's a template
      to ensure the static file anti-cache versioning by
      query string works.
      
    """
    
    def get(self, *args):
        return self.render_template('bespin.tmpl')
        
    
    

