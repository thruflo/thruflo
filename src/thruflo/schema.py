#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Form schemas for validation.
"""

import re

import formencode
from formencode import validators

valid_slug = re.compile(r'^\w{3,18}$', re.U)
valid_document_id = re.compile(r'^[a-z0-9]{32}$', re.U)

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
        
    
    


class AddOrEditDocument(formencode.Schema):
    """
    """
    
    display_name = validators.UnicodeString(not_empty=True)
    

class Insert(formencode.Schema):
    
    # what to insert
    repo = validators.UnicodeString(not_empty=True)
    branch = validators.UnicodeString(not_empty=True)
    path = validators.UnicodeString(not_empty=True)
    
    # where to insert it (ooh err missus)
    index = validators.Int(not_empty=True)
    

