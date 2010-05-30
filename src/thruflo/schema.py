#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Form schemas for validation, independent of the models.
"""

import re

valid_slug = re.compile(r'^\w{3,18}$', re.U)
valid_document_id = re.compile(r'^[a-z0-9]{32}$', re.U)
valid_github_sha = re.compile(r'^[a-z0-9]{40}$', re.U)

import formencode
from formencode import validators

import utils

class Slug(validators.UnicodeString):
    """Lowercase, no spaces, no funny chars, between 3 and 18 long.
    """
    
    messages = {
        'invalid': 'No spaces, no funny chars, between 3 and 18 long.'
    }
    
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
        
    
    

class CouchDocumentId(validators.UnicodeString):
    """``uuid.uuid4``
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
        
    
    

class GithubSha(validators.UnicodeString):
    """``7deda716d140efd40f85f44f1fcef86c392ee5d7``
    """
    
    messages = {'invalid': 'Invalid hash'}
    
    def _to_python(self, value, state):
        value = super(GithubSha, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(GithubSha, self).validate_python(value, state)
        if not valid_github_sha.match(value):
            raise validators.Invalid(
                self.message("invalid", state),
                value,
                state
            )
        
    
    

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
        
    
    


class RequiredSlug(formencode.Schema):
    slug = Slug(not_empty=True)

class Repository(formencode.Schema):
    """
    """
    
    name = validators.UnicodeString(not_empty=True)
    owner = validators.UnicodeString(not_empty=True)
    url = validators.UnicodeString(not_empty=True)
    

class AddOrEditDocument(formencode.Schema):
    """
    """
    
    display_name = validators.UnicodeString(not_empty=True)
    

class UpdateDocument(formencode.Schema):
    """
    """
    
    sources = validators.Set()
    stylesheet = validators.UnicodeString()
    content = validators.UnicodeString()
    

class Insert(formencode.Schema):
    
    # what to insert
    repo = validators.UnicodeString(not_empty=True)
    branch = validators.UnicodeString(not_empty=True)
    path = validators.UnicodeString(not_empty=True)
    
    # where to insert it (ooh err missus)
    index = validators.Int(not_empty=True)
    

