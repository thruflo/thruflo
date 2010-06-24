#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Form schemas for validation, independent of the models.
"""

import formencode
from formencode import validators

import logging
import markdown
import re

from thruflo.webapp.utils import generate_hash

import model

slug_pattern = r'[0-9]{8}'
valid_slug = re.compile(r'^%s$' % slug_pattern, re.U)

username_pattern = r'[.\-\w]{3,18}'
valid_username = re.compile(r'^%s$' % username_pattern, re.U)

document_id_pattern = r'[a-z0-9]{32}'
valid_document_id = re.compile(r'^%s$' % document_id_pattern, re.U)

class Slug(validators.UnicodeString):
    """An eight digit string.
    """
    
    messages = {'invalid': 'Invalid slug.'}
    
    def _to_python(self, value, state):
        value = super(Slug, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(Slug, self).validate_python(value, state)
        if not valid_slug.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
        
    
    

class Username(validators.UnicodeString):
    """Lowercase, no spaces, no funny chars, between 3 and 18 long.
    """
    
    messages = {
        'invalid': 'No spaces, no funny chars, between 3 and 18 long.'
    }
    
    def _to_python(self, value, state):
        value = super(Username, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(Username, self).validate_python(value, state)
        if not valid_username.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
            
        
    
    

class CouchDocumentId(validators.UnicodeString):
    """``uuid.uuid4``.
    """
    
    messages = {
        'invalid': 'Invalid document id'
    }
    
    def _to_python(self, value, state):
        value = super(CouchDocumentId, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(CouchDocumentId, self).validate_python(value, state)
        if not valid_document_id.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    
    

class SecurePassword(validators.UnicodeString):
    """Hashes the user input before we do anything with it.
      Means we don't store raw passwords.
    """
    
    def _to_python(self, value, state):
        value = super(SecurePassword, self)._to_python(value, state)
        return generate_hash(s=value.strip().lower())
        
    
    

class UnicodeEmail(validators.Email):
    """Overwrite ``validators.Email`` with 
      ``validators.UnicodeString``s ``_to_python`` method.
    """
    
    def _to_python(self, value, state):
        if not value:
            return u''
        if isinstance(value, unicode):
            return value
        if not isinstance(value, unicode):
            if hasattr(value, '__unicode__'):
                value = unicode(value)
                return value
            else:
                value = str(value)
        try:
            return unicode(value, 'utf-8')
        except UnicodeDecodeError:
            raise validators.Invalid(
                self.message('badEncoding', state), value, state
            )
        except TypeError:
            raise validators.Invalid(
                self.message(
                    'badType', state, type=type(value), value=value
                ), 
                value, state
            )
        
    
    

class UniqueUsername(Username):
    """Check to see that a username doesn't exist.
    """
    
    messages = {
        'taken': u'%(username)s has already been taken.'
    }
    
    def validate_python(self, value, state):
        super(UniqueUsername, self).validate_python(value, state)
        if model.User.check_exists(value):
            raise validators.Invalid(
                self.message("taken", state, username=value),
                value, 
                state
            )
        
        
    
    

class UniqueEmail(UnicodeEmail):
    """Check to see that an email doesn't already exist.
    """
    
    messages = {
        'taken': u'%(email_address)s has already been registered.'
    }
    
    def _to_python(self, value, state):
        value = super(UniqueEmail, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(UniqueEmail, self).validate_python(value, state)
        if model.User.view('user/email', key=value).first():
            raise validators.Invalid(
                self.message("taken", state, email_address=value),
                value, 
                state
            )
        
        
    
    


class Register(formencode.Schema):
    username = UniqueUsername(not_empty=True)
    password = SecurePassword(not_empty=True)
    confirm = SecurePassword(not_empty=True)
    chained_validators = [
        validators.FieldsMatch(
            'password', 
            'confirm'
        )
    ]
    name = validators.UnicodeString(not_empty=True)
    email = UniqueEmail(resolve_domain=True, not_empty=True)
    

class Login(formencode.Schema):
    username = Username(not_empty=True)
    password = SecurePassword(not_empty=True)
    


path_pattern = r'/([ \-\.\w]+\/?)*'
valid_path = re.compile(r'^%s$' % path_pattern, re.U)

content_pattern = r'^<h1>'
valid_content = re.compile(content_pattern, re.U)

class Content(validators.UnicodeString):
    """Parses the content into html with `Python-Markdown`_
      and enforces that the html must start with an ``<h1>``.
      
      .. _`Python-Markdown`: http://www.freewisdom.org/projects/python-markdown
      
    """
    
    messages = {'invalid': 'Invalid content.'}
    
    def _to_python(self, value, state):
        value = super(Content, self)._to_python(value, state)
        return markdown.markdown(value)
        
    
    
    def validate_python(self, value, state):
        super(Content, self).validate_python(value, state)
        logging.debug(value)
        if not valid_content.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    
    

class Path(validators.UnicodeString):
    """A ``/unix/style/url/pathy/whatnot\/?``.
    """
    
    messages = {'invalid': 'Invalid path.'}
    
    def _to_python(self, value, state):
        value = super(Path, self)._to_python(value, state)
        return value.strip()
        
    
    def validate_python(self, value, state):
        super(Path, self).validate_python(value, state)
        if not valid_path.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    
    


class Save(formencode.Schema):
    content = Content(not_empty=True)
    path = Path(not_empty=True)
    

