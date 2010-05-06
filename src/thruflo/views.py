#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Request handlers for the human web interface.
"""

import functools
import logging
import time
import uuid

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
    'Index', 'Login', 'Logout', 'Register', 'NotFound',
    'Dashboard', 'Documents', 'Projects', 'Themes', 'Deliverables'
]

class RequestHandler(web.RequestHandler):
    """Base RequestHandler that:
      
      #. gets ``self.current_user`` from a secure cookie
      #. provides ``self.render_tmpl(tmpl_name, **kwargs)`` method
         using mako templates
      
      @@: ``self.current_user`` and ``self.account`` both hit the db
          *every request*, which is somewhat suboptimal ;)
      
    """
    
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        if user_id:
            return model.db.query(model.User).get(int(user_id))
        return None
        
    
    
    @property
    def account(self):
        if not hasattr(self, "_account"):
            self._account = self.get_account()
        return self._account
        
    
    def get_account(self):
        host = self.request.host
        parts = host.split(self.settings['domain'])
        account_slug = parts[0]
        if account_slug:
            account_slug = account_slug[:-1]
            query = model.db.query(model.Account)
            return query.filter_by(slug=account_slug).first()
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
            
        self.redirect(path)
        
    
    
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
        if self.account:
            self.redirect('/dashboard')
        else:
            self.render_tmpl('index.tmpl')
        
        
    
    


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
                        domain='.%s' % self.settings['domain']
                    )
                    self.redirect_to_dashboard(user)
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
    """If we get valid form input, we create a user, store their 
      user.id in a secure cookie and redirect to their dashboard.
    """
    
    @property
    def timezones(self):
        return get_timezones()
    
    
    def post(self):
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
                    domain='.%s' % self.settings['domain']
                )
                self.redirect_to_dashboard(user)
                
            
        
        
    
    
    def get(self):
        self.render_tmpl('register.tmpl', errors={})
        
    
    


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
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + unicode_urlencode(
                        dict(next=self.request.path)
                    )
                self.redirect(url)
                return
            raise web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
    
    


class SlugMixin(object):
    """Couchdb ``doc._id``s are long ``uuid4``s which is great
      for avoiding conflicts but too long to feature nicely in
      a user friendly URL.
      
      Equally, there's no reason we need to ask users to provide
      a slug when creating something.
      
      So, we need a mechanism to generate shorter, more user 
      friendly identifiers that can be used as the value of the 
      an instance's ``slug`` property.  These need to be fairly 
      unique, so it's very rare they would clash within a document
      type, within an account.
      
      We also need a sensible approach to conflicts, which is to
      manually re-slug the newer instance until there is only one.
      
      Plus we check when generating a slug that it's unique.
      
      All in all, overkill.  Which is good.
    """
    
    def generate_slug(self):
        """Generates a random seven digit unicode string.
        """
        
        return unicode(uuid.uuid4().int)[:7]
        
    
    def get_from_slug(self, slug, document_class):
        docs = document_class.view(
            'all/type_slug_mod',
            startkey=[
                self.account.id,
                document_class._doc_type,
                slug,
                False
            ],
            endkey=[
                self.account.id,
                document_class._doc_type,
                slug,
                []
            ],
            include_docs=True
        ).all()
        if len(docs) == 0:
            return None
        elif len(docs) > 1:
            newer = docs[1:]
            newer.reverse()
            for doc in newer:
                doc.slug = self.generate_slug()
                doc.save()
        return docs[0]
        
    
    def get_unique_slug(self, document_class, max_tries=5):
        i = 1
        while True:
            if i > max_tries:
                raise Exception('Can\'t generate unique slug')
            else:
                slug = self.generate_slug()
                if not self.get_from_slug(slug, document_class):
                    break
                else:
                    i += 1
        return slug
        
    
    


class Dashboard(RequestHandler):
    """
    """
    
    @members_only
    def get(self):
        self.render_tmpl('dashboard.tmpl')
    
    

class Documents(RequestHandler):
    """
    """
    
    @members_only
    def get(self):
        self.render_tmpl('documents.tmpl')
        
    
    

class Projects(RequestHandler, SlugMixin):
    """
    """
    
    def add(self):
        """Add a new project:
            
            #. ``/projects/:slug/add``
          
        """
        
        params = {
            'display_name': self.get_argument('display_name', None)
        }
        try:
            params = schema.Project.to_python(params)
        except formencode.Invalid, err:
            return err.error_dict
        else:
            params['account_id'] = self.account.id
            params['slug'] = self.get_unique_slug(model.Project)
            project = model.Project(**params)
            project.save()
            self.redirect('/projects/%s' % project.slug)
            
        
    
    def edit(self):
        """Edit project metadata:
            
              #. ``/projects/:slug/edit?display_name=...``
            
        """
        
        params = {
            'display_name': self.get_argument('display_name', None)
        }
        try:
            params = schema.Project.to_python(params)
        except formencode.Invalid, err:
            return {'status': 500, 'errors': err.error_dict}
        else:
            self.project.display_name = params['display_name']
            self.project.save()
            return {'status': 200, 'doc': self.project.to_json()}
            
        
    
    def save(self, section_type):
        """Overwrite a project section.
          
            #. ``/projects/:slug/save/solution?content=...``
            #. ``...save/solution?project_section_id=...&content=...``
        """
        
        params = {
            'section_type': section_type,
            'content': self.get_argument('content', None)
        }
        try:
            params = schema.ProjectSection.to_python(params)
        except formencode.Invalid, err:
            return {'status': 500, 'errors': err.error_dict}
        else:
            psid = self.get_argument('project_section_id', None)
            if psid:
                try:
                    psid = schema.Slug.to_python(psid)
                except formencode.Invalid, err:
                    return {
                        'status': 500, 
                        'errors': {'project_section_id': unicode(err)}
                    }
                else:
                    doc = model.ProjectSection.get(psid)
                    check_one = doc.section_type == section_type
                    check_two = doc.project_id == self.project.id
                    if check_one and check_two:
                        doc.content = params['content']
                    else:
                        return {
                            'status': 500, 
                            'errors': {'project_section_id': u'Invalid'}
                        }
            else:
                doc = model.ProjectSection(
                    account_id=self.account.id,
                    project_id=self.project.id,
                    **params
                )
            doc.save()
            return {'status': 200, 'doc': doc.to_json()}
        
    
    def fork(self, section_type):
        """Duplicate a project section.
          
            #. ``/projects/:slug/fork/solution?project_section_id=...
        """
        
        psid = self.get_argument('project_section_id', None)
        if psid:
            try:
                psid = schema.Slug.to_python(psid)
            except formencode.Invalid, err:
                return {
                    'status': 500, 
                    'errors': {'project_section_id': unicode(err)}
                }
            else:
                doc = model.ProjectSection.get(psid)
                check_one = doc.section_type == section_type
                check_two = doc.project_id == self.project.id
                if check_one and check_two:
                    duplicate = mode.ProjectSection(
                        account_id=self.account.id,
                        project_id=self.project.id,
                        section_type=doc.section_type,
                        content=doc.content
                    )
                    duplicate.save()
                    return {'status': 200, 'doc': duplicate.to_json()}
                else:
                    return {
                        'status': 500, 
                        'errors': {'project_section_id': u'Invalid'}
                    }
                
            
        
    
    
    @property
    def projects(self):
        return model.Project.view(
            'all/type_slug_mod',
            startkey=[self.account.id, 'Project', False, False],
            endkey=[self.account.id, 'Project', [], []],
            include_docs=True
        ).all()
    
    
    @property
    def project_sections(self):
        results = model.Project.view(
            'project/all',
            startkey=[
                self.account.id, 
                self.project.id, 
                False, 
                False
            ],
            endkey=[self.account.id, self.project.id, [], []],
            include_docs=True
        )
        sections_by_type = {}
        for item in results:
            k = item.section_type
            if sections_by_type.has_key():
                sections_by_type[k].append(item)
            else:
                sections_by_type[k] = [item]
        return sections_by_type
        
    
    
    @members_only
    def post(self, *args):
        """Dispatches ``/projects/add`` to ``self.add()`` and
          ``/projects/:slug/:action`` to ``self.action()``, passing
          through any addtional args.
        """
        
        if args[0] == 'add':
            error_dict = self.add()
            self.render_tmpl('projects.tmpl', errors=error_dict)
        else:
            slug = args[0]
            self.project = self.get_from_slug(slug, model.Project)
            if self.project:
                method = getattr(self, args[1])
                data = method(*args[2:])
            self.set_header(
                'Content-Type', 
                'application/json; charset=UTF-8'
            )
            self.response.out.write(json_encode(data))
        
    
    
    @members_only
    def get(self, slug=None):
        project = None
        if slug:
            self.project = self.get_from_slug(slug, model.Project)
            if self.project:
                self.render_tmpl('project.tmpl')
            else:
                self.render_tmpl('404.tmpl')
        else:
            self.render_tmpl('projects.tmpl', errors={})
        
    
    

class Themes(RequestHandler):
    """
    """
    
    @members_only
    def get(self):
        self.render_tmpl('themes.tmpl')
        
    
    

class Deliverables(RequestHandler):
    """
    """
    
    @members_only
    def get(self):
        self.render_tmpl('deliverables.tmpl')
        
    
    


class NotFound(RequestHandler):
    """
    """
    
    def get(self):
        self.render_tmpl('404.tmpl')
        
    
    


