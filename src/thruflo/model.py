#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Properties, schemas and db bindings.
  
  We use Couchdb_ to store and index data and Couchdbkit_
  as a python wrapper / bindings.
  
  Couchdbkit_ provides a nice 'starting point schema' pattern
  which works like a normal ORM for defining properties
  and schemas and handles serialisation from python to couch
  and back again.
  
  These schemas are also dynamic, so you can just add any old
  property you want to an instance.  See the docs_ for more.
  
  .. _Couchdb: http://couchdb.apache.org/
  .. _Couchdbkit: http://couchdbkit.org/
  .. _docs: http://couchdbkit.org/docs/gettingstarted.html
"""

__all__ = [
    'SlugProperty', 'EmailProperty', 'PasswordProperty',
    'dbs', 'User', 'Account',
    'Template', 'Document', 'Topic',
    'Project', 'ProjectSection',
    'Deliverable', 'DeliverableSection'
]

import datetime
import logging
import re

from os.path import dirname, join as join_path

from fv_email import Email as EmailValidator

from couchdbkit import Document, Server, ResourceNotFound, ResourceConflict
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema.properties import *

from utils import generate_hash

valid_slug = re.compile(r'^\w{3,18}$', re.U)
valid_password = re.compile(r'^\S{6,72}$', re.U)
class SlugProperty(StringProperty):
    """Makes sure any candidate values for slugs ids are simple
      alphanumeric with no funny stuff.
    """
    
    def validate(self, value, **kwargs):
        # normal unicode validation
        value = super(SlugProperty, self).validate(value, **kwargs)
        if value is None:
            return value
        # special slug validation
        if not valid_slug.match(value):
            raise ValueError(
                u'%s can only contain letters, numbers and the underscore,\
                and must be between 3 and 18 characters long' % value
            )
        return value
        
    
    

class EmailProperty(StringProperty):
    """Validates against syntax *and* dns lookup.
    """
    
    def validate(self, value, **kwargs):
        # normal unicode validation
        value = super(EmailProperty, self).validate(value, **kwargs)
        if value is None:
            return value
        # special email validation
        return EmailValidator(resolve_domain=True).to_python(value)
        
    
    

class PasswordProperty(StringProperty):
    """Hashes the input.
    """
    
    def validate(self, value, **kwargs):
        # normal unicode validation
        value = super(PasswordProperty, self).validate(value, **kwargs)
        if value is None:
            return value
        value = value.lower().strip()
        if not valid_password.match(value):
            raise ValueError(u'Must be at least 6 characters with no spaces')
        else: # convert password to a sha-1 hash
            return generate_hash(s=value)
        
    
    


class Model(Document):
    """Extensions to the couchdbkit base class.
    """
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    def update(self, data):
        """Convienience method for setting multiple properties.
        """
        
        for k, v in data.iteritems():
            setattr(self, k, v)
        
        
    

class MultiDBModel(Model):
    """Overwrites methods of the base ``Model`` class that
      prescribe a fixed mapping between class and database.
      
      Can be used like normal but can also pass ``db=...``
      to methods as necessary.
    """
    
    def save(self, db=None, **params):
        """ Save document in database.
        """
        
        self.validate()
        
        if self._db is None and db is None:
            raise TypeError("doc database required to save document")
        else:
            _db = self._db and self._db or db
        
        doc = self.to_json()
        _db.save_doc(doc, **params)
        if '_id' in doc and '_rev' in doc:
            self._doc.update(doc)
        elif '_id' in doc:
            self._doc.update({'_id': doc['_id']})
        
    
    
    @classmethod
    def bulk_save(cls, docs, use_uuids=True, all_or_nothing=False):
        """ Save multiple documents in database.
        """
        
        if cls._db is None and db is None:
            raise TypeError("doc database required to save document")
        else:
            _db = cls._db and cls._db or db
        
        docs_to_save= [doc._doc for doc in docs if doc._doc_type == cls._doc_type]
        if not len(docs_to_save) == len(docs):
            raise ValueError("one of your documents does not have the correct type")
        
        _db.bulk_save(
            docs_to_save, 
            use_uuids=use_uuids, 
            all_or_nothing=all_or_nothing
        )
        
    
    
    @classmethod
    def get(cls, docid, rev=None, db=None, dynamic_properties=True):
        """Get document with `docid`
        """
        
        if cls._db is None and db is None:
            raise TypeError("doc database required to save document")
        else:
            _db = cls._db and cls._db or db
        cls._allow_dynamic_properties = dynamic_properties
        return _db.get(docid, rev=rev, wrapper=cls.wrap)
        
    
    
    @classmethod
    def get_or_create(cls, docid=None, db=None, dynamic_properties=True, **params):
        """Get or create document with `docid`
        """
        
        if cls._db is None and db is None:
            raise TypeError("doc database required to save document")
        else:
            _db = cls._db and cls._db or db
        cls._allow_dynamic_properties = dynamic_properties
        
        if docid is None:
            obj = cls()
            obj.save(db=_db, **params)
            return obj
        rev = params.pop('rev', None)
        
        try:
            return _db.get(docid, rev=rev, wrapper=cls.wrap, **params)
        except ResourceNotFound:
            obj = cls()
            obj._id = docid
            obj.save(db=_db, **params)
            return obj
        
    
    
    @classmethod
    def __view(
            cls, view_type=None, data=None, wrapper=None,
            dynamic_properties=True, wrap_doc=True, 
            db=None, **params
        ):
        def default_wrapper(row):
            data = row.get('value')
            docid = row.get('id')
            doc = row.get('doc')
            if doc is not None and wrap_doc:
                cls._allow_dynamic_properties = dynamic_properties
                return cls.wrap(doc)
            elif not data or data is None:
                return row
            elif not isinstance(data, dict) or not docid:
                return row
            else:
                data['_id'] = docid
                if 'rev' in data:
                    data['_rev'] = data.pop('rev')
                cls._allow_dynamic_properties = dynamic_properties
                return cls.wrap(data)
        if wrapper is None:
            wrapper = default_wrapper
        if not wrapper:
            wrapper = None
        elif not callable(wrapper):
            raise TypeError("wrapper is not a callable")
        try:
            _db = cls.get_db()
        except TypeError:
            if db is not None:
                _db = db
            else:
                raise
        if view_type == 'view':
            return _db.view(data, wrapper=wrapper, **params)
        elif view_type == 'temp_view':
            return _db.temp_view(data, wrapper=wrapper, **params)
        else:
            raise RuntimeError("bad view_type : %s" % view_type )
        
    
    
    def delete(self, db=None):
        """Delete document from the database.
        """
        
        if self._db is None and db is None:
            raise TypeError("doc database required to delete document")
        else:
            _db = self._db and self._db or db
        
        if self.new_document:
            raise TypeError("the document is not saved")
        
        _db.delete_doc(self._id)
        
        # reinit document
        del self._doc['_id']
        del self._doc['_rev']
        
    
    


class CouchDBs(object):
    """Provides ``self.{db_name}`` for each ``couchdb`` database
      and a ``sync`` method to sync the dbs with the view code 
      from ``./_design``.
    """
    
    fixed_dbs = [
        'users'
    ]
    account_dbs = [
        # created per user account on sign up
    ]
    
    def sync(self):
        """Sync the views from the filesystem for each database.
        """
        
        for item in self.fixed_dbs:
            views = join_path(dirname(__file__), '_design', item)
            loader = FileSystemDocsLoader(views)
            db = getattr(self, item)
            loader.sync(db)
        
        for item in self.account_dbs:
            views = join_path(dirname(__file__), '_design', 'accounts')
            loader = FileSystemDocsLoader(views)
            db = getattr(self, item)
            loader.sync(db)
            
        
    
    
    def __init__(self, sync=False):
        s = Server()
        l = s.all_dbs()
        for item in self.fixed_dbs:
            setattr(self, item, s.get_or_create_db(item))
            if item in l:
                l.remove(item)
        self.account_dbs = l
        for item in self.account_dbs:
            setattr(self, item, s.get_or_create_db(item))
        
    
    

dbs = CouchDBs()

class User(Model):
    """Sign up requires username, password and email_address.
      
      Login requires username or email_address, plus password.
      Password is stored as a hash.
      
      Provides ``authenticate(username_or_email, password)``
      method. 
    """
    
    username = SlugProperty(required=True)
    password = PasswordProperty(required=True)
    
    email_address = EmailProperty(required=True)
    #time_zone = TimeProperty(required=True)
    
    first_name = StringProperty()
    last_name = StringProperty()
    company = StringProperty()
    
    is_suspended = BooleanProperty(default=False)
    has_confirmed = BooleanProperty(default=False)
    
    confirmation_hash = StringProperty()
    
    administrator_accounts = StringListProperty()
    member_accounts = StringListProperty()
    
    @classmethod
    def authenticate(cls, identifier, password):
        return User.view(
            'users/authenticate',
            key=[identifier, password],
            include_docs=True
        ).one()
        
    
    

User.set_db(dbs.users)

class Account(MultiDBModel):
    """One ``Account`` metadata entity per database.
    """
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    
    plan = StringProperty(
        required=True, choices=[
            'basic', 'plus', 'premium', 'max'
        ]
    )
    


class Template(MultiDBModel):
    """
    """
    
    content = StringProperty()
    

class Document(MultiDBModel):
    """
    """
    
    parts = StringListProperty()
    


project_section_types = [
    'brief', 'solution', 'results'
]
class Project(MultiDBModel):
    """
    """
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    

class ProjectSection(MultiDBModel):
    """
    """
    
    project_id = SlugProperty(required=True)
    section_type = StringProperty(
        required=True, 
        choices=project_section_types
    )
    content = StringProperty()
    


class Topic(MultiDBModel):
    """"""
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    
    content = StringProperty()
    


deliverable_section_types = [
    'budget', 'process', 'time'
]
class Deliverable(MultiDBModel):
    """
    """
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    

class DeliverableSection(MultiDBModel):
    """
    """
    
    project_id = SlugProperty(required=True)
    section_type = StringProperty(
        required=True, 
        choices=deliverable_section_types
    )
    content = StringProperty()
    


def main():
    """Sync the couch db views.
    """
    
    dbs.sync()


if __name__ == '__main__':
    main()

