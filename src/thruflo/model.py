#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""We persist data in couchdb_ via Couchdbkit_.
  
  .. _couchdb: http://couchdb.apache.org/
  .. _Couchdbkit: http://couchdbkit.org/
"""

__all__ = [
    'User', 
    'Repository',
    'Document',
]

import logging
import uuid

from os.path import dirname, join as join_path

from couchdbkit import Server, ResourceNotFound, ResourceConflict
from couchdbkit import Document as CouchDBKitDocument
from couchdbkit.exceptions import BulkSaveError
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema.properties import *

from thruflo.webapp.utils import generate_hash

import config

class Couch(object):
    """Convenience wrapper around the ``couchdbkit``
      ``Server`` and ``FileSystemDocsLoader`` internals.
      
      Provides the ``couchdbkit.Database`` called "thruflo"
      as ``self.db``.
    """
    
    def sync(self):
        path = join_path(dirname(__file__), '_design')
        self.loader = FileSystemDocsLoader(path)
        self.loader.sync(self.db)
        
    
    
    def __init__(self, sync=config.debug):
        self.db = Server().get_or_create_db('thruflo')
        if sync:
            self.sync()
        
    
    

couch = Couch()

class BaseDocument(CouchDBKitDocument):
    """Tweak Couchdbkit a little and extends it to provide ``ver``
      ``mod`` and ``archived``.
    """
    
    @classmethod
    def soft_get(cls, docid, default=None):
        """Allows::
          
              inst = cls.soft_get(possible_id)
              if not inst: 
                  # possible_id didn't exist
              
          
        """
        
        try:
            return cls.get(docid)
        except ResourceNotFound:
            return default
        
        
    
    
    @classmethod
    def get_or_create(
            cls, 
            docid=None, 
            db=None, 
            dynamic_properties=True, 
            **params
        ):
        """There's a bug passing params to the original version 
          of this method.  The only change made here is to not pass
          ``**params`` to ``cls._db.get()``.
        """
        
        if db is not None:
            cls._db = db
        
        cls._allow_dynamic_properties = dynamic_properties
        
        if cls._db is None:
            raise TypeError("doc database required to save document")
        if docid is None:
            raise ValueError("why use ``get_or_create`` without a ``docid``?")
        
        rev = params.pop('rev', None)
        
        try:
            return cls._db.get(docid, rev=rev, wrapper=cls.wrap)
        except ResourceNotFound:
            obj = cls()
            obj._id = docid
            obj.update(params)
            obj.save()
            return obj
        
    
    
    
    def __getattr__(self, key):
        """We like using ``doc.id``.
        """
        
        if key == 'id':
            key = '_id'
        return super(BaseDocument, self).__getattr__(key)
        
    
    
    def update(self, data):
        """Convienience method for setting multiple properties
          at once from a dictionary.
        """
        
        for k, v in data.iteritems():
            setattr(self, k, v)
            
        
    
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    archived = BooleanProperty(default=False)
    

class SluggedDocument(BaseDocument):
    """Couchdb ``doc._id``s are long ``uuid4``s which is great
      for avoiding conflicts but too long to feature nicely in
      a user friendly URL.
      
      Equally, there's no reason we need to ask users to provide
      a slug when creating something.
      
      So, we need a mechanism to generate shorter, more user 
      friendly identifiers that can be used as the value of the 
      an instance's ``slug`` property.  
      
      Whilst we check when generating a slug that it's unique,
      they need to be fairly unique, so it's very rare they 
      would clash within a document type, within an account.
      
      We also need a sensible approach to conflicts, which is to
      manually re-slug the newer instance until there is only one.
    """
    
    @classmethod
    def generate_slug(cls):
        """Generates a random eight digit string.
        """
        
        return str(uuid.uuid4().int)[:8]
        
    
    
    @classmethod
    def get_from_slug(cls, namespace, slug):
        docs = cls.view(
            'slugged/type_namespace_slug_mod',
            startkey=[cls._doc_type, namespace, slug, None],
            endkey=[cls._doc_type, namespace, slug, []],
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
        
    
    
    @classmethod
    def get_unique_slug(cls, namespace, max_tries=5):
        i = 1
        while True:
            if i > max_tries:
                raise Exception('Can\'t generate unique slug')
            else:
                slug = cls.generate_slug()
                if not cls.get_from_slug(namespace, slug):
                    break
                else:
                    i += 1
        return slug
        
    
    
    namespace = StringProperty(required=True)
    slug = StringProperty(required=True)
    

BaseDocument.set_db(couch.db)

class User(BaseDocument):
    """``User``s can own and share ``Repository``s.
    """
    
    username = StringProperty(required=True)
    password = StringProperty(required=True)
    
    name = StringProperty(required=True)
    email = StringProperty(required=True)
    
    # repositories
    owned = StringListProperty()
    shared = StringListProperty()
    
    @property
    def repositories(self):
        """List of ``repository.id``s this user can access.
        """
        
        return self.owned + self.shared
        
    
    
    @classmethod
    def _get_id_from_username(cls, username):
        """We use a hash of the ``username`` as the ``user.id``.
        """
        
        return 'user%s' % generate_hash(s=username)
        
    
    
    @classmethod
    def check_exists(cls, username):
        candidate_id = cls._get_id_from_username(username)
        return candidate_id in cls.get_db()
        
    
    
    @classmethod
    def create_user(cls, username, params):
        candidate_id = cls._get_id_from_username(username)
        user = cls(_id=candidate_id, **params)
        try:
            user.save()
        except ResourceConflict:
            return None
        else:
            return user
        
        
    
    
    @classmethod
    def authenticate(cls, username, password):
        return cls.view(
            'user/authenticate', 
            key=[
                username,
                password
            ],
            include_docs=True
        ).one()
        
    
    

class Repository(SluggedDocument):
    """``Repository``s are slugged, so they can be accessed
      by URL like ``../repo/73652037`` rather than the rather
      unweildy ``../repo/d8sjd6dhd8dkd0s9a6sme5w6dks7sm35``
    """
    
    # display name
    name = StringProperty(default=u'Default')
    

class Document(BaseDocument):
    """``Repository``s contain ``Document``s.
    """
    
    repository = StringProperty(required=True)
    path = StringProperty(required=True)
    
    content = StringProperty()
    


def sync():
    """Syncs the couchdb views in the database with the 
      ``./_design`` folder.
    """
    
    couch.sync()
    

