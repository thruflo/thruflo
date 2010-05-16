#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Form schemas for validation, independent of the models.
"""

__all__ = [
    'RequiredSlug', 'Registration', 'Login', 
    'Document', 'ProjectSection'
]

import re

import formencode
from formencode import validators

import model
from utils import get_timezones, generate_hash

slug_pattern = r'\w{3,18}'
valid_slug = re.compile(r'^%s$' % slug_pattern, re.U)

document_id_pattern = r'[a-z0-9]{32}'
valid_document_id = re.compile(r'^%s$' % document_id_pattern, re.U)

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
            return unicode(value, self.inputEncoding)
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
        
    
    

class Timezone(validators.UnicodeString):
    """Must be in ``utils.get_timezones()``.
    """
    
    messages = {
        'invalid': 'That\'s not a valid timezone'
    }
    
    def _to_python(self, value, state):
        value = super(Timezone, self)._to_python(value, state)
        return value.strip()
        
    
    
    def validate_python(self, value, state):
        super(Timezone, self).validate_python(value, state)
        timezones = get_timezones()
        match = False
        try:
            parts = value.split(' ')
            v = (parts[1], parts[0])
        except (ValueError, IndexError):
            raise validators.Invalid(
                self.message("invalid", state),
                value, 
                state
            )
        else:
            for item in timezones:
                if v == item:
                    match = True
                    break
        if not match:
            raise validators.Invalid(
                self.message("invalid", state),
                value, 
                state
            )
        
    
    

class UniqueUsername(Slug):
    """Courtesy check to see that a username doesn't exist,
      prior to uniqueness being enforced by constraint.
    """
    
    messages = {
        'taken': u'%(username)s has already been taken. Please choose another username.'
    }
    
    def validate_python(self, value, state):
        super(UniqueUsername, self).validate_python(value, state)
        if model.db.query(model.User).filter_by(username=value).first():
            raise validators.Invalid(
                self.message("taken", state, username=value),
                value, 
                state
            )
        
    
    

class UniqueEmail(UnicodeEmail):
    """Courtesy check to see that a username doesn't exist,
      prior to uniqueness being enforced by constraint.
    """
    
    messages = {
        'taken': u'%(email_address)s has already been registered.'
    }
    
    def _to_python(self, value, state):
        value = super(UniqueEmail, self)._to_python(value, state)
        return value.strip().lower()
        
    
    
    def validate_python(self, value, state):
        super(UniqueEmail, self).validate_python(value, state)
        if model.db.query(model.User).filter_by(email_address=value).first():
            raise validators.Invalid(
                self.message("taken", state, email_address=value),
                value, 
                state
            )
        
    
    

class UniqueAccountSlug(Slug):
    """Courtesy check to see that a slug doesn't exist,
      prior to uniqueness being enforced by constraint.
    """
    
    messages = {
        'taken': u'%(slug)s has already been taken. Please choose another site name.'
    }
    
    def validate_python(self, value, state):
        super(UniqueAccountSlug, self).validate_python(value, state)
        if model.db.query(model.Account).filter_by(slug=value).first():
            raise validators.Invalid(
                self.message("taken", state, slug=value),
                value, 
                state
            )
        
    
    


class RequiredSlug(formencode.Schema):
    slug = Slug(not_empty=True)


class Registration(formencode.Schema):
    """
    """
    
    first_name = validators.UnicodeString(not_empty=True)
    last_name = validators.UnicodeString(not_empty=True)
    email_address = UniqueEmail(resolve_domain=True, not_empty=True)
    company = validators.UnicodeString()
    time_zone = Timezone(not_empty=True)
    
    username = UniqueUsername(not_empty=True)
    password = SecurePassword(not_empty=True)
    confirm = SecurePassword(not_empty=True)
    chained_validators = [
        validators.FieldsMatch(
            'password', 
            'confirm'
        )
    ]
    
    account = UniqueAccountSlug(not_empty=True)
    

class Login(formencode.Schema):
    """
    """
    
    username = Slug(not_empty=True)
    email_address = UnicodeEmail(resolve_domain=True, not_empty=True)
    
    password = SecurePassword(not_empty=True)
    


class DisplayNamed(formencode.Schema):
    display_name = validators.UnicodeString(not_empty=True)

class ContentSection(formencode.Schema):
    slug = Slug(not_empty=True)
    section_type = Slug(not_empty=True)
    branch_name = Slug(not_empty=True)
    content = validators.UnicodeString()
    


class Document(formencode.Schema):
    display_name = validators.UnicodeString(not_empty=True)
    document_type = validators.OneOf(model.document_types)

class Section(formencode.Schema):
    """"""
    

class Unit(formencode.Schema):
    """"""
    

