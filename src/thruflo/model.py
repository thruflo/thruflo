#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""We use a relational database for users and accounts and couchdb_
  (via Couchdbkit_) for the per-account document data.
  
  .. _couchdb: http://couchdb.apache.org/
  .. _Couchdbkit: http://couchdbkit.org/
"""

import copy
import datetime
import logging
import os
import re
import sys
import uuid

from os.path import dirname, join as join_path

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import Float, Integer, Unicode, Boolean, DateTime, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation

if sys.platform == 'darwin': # use sqlite in development
    engine = create_engine('sqlite:////env/thruflo/var/dev.db')
else: # use postgresql in production with a
    import secret # pure-python driver so we take advantage of gevent
    engine = create_engine( 
        'postgresql+pg8000://%s:%s@%s/%s' % (
            secret.username,
            secret.password,
            secret.host,
            secret.dbname
        )
    )
SQLModel = declarative_base()

# many to many relation between ``User``s and ``Account``s
admins = Table(
    'admins',
    SQLModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('account_id', Integer, ForeignKey('accounts.id'))
)
members = Table(
    'members',
    SQLModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('account_id', Integer, ForeignKey('accounts.id'))
)

class User(SQLModel):
    """Sign up requires username, password and email_address.
      
      Login requires username or email_address, plus password.
      Password is stored as a hash.
      
      Provides ``authenticate(username_or_email, password)``
      method. 
    """
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, nullable=False)
    
    username = Column(Unicode, unique=True)
    email_address = Column(Unicode, unique=True)
    password = Column(Unicode)
    
    first_name = Column(Unicode)
    last_name = Column(Unicode)
    time_zone = Column(Integer)
    
    github_username = Column(Unicode)
    github_token = Column(Unicode)
    
    is_suspended = Column(Boolean, default=False)
    has_confirmed = Column(Boolean, default=False)
    
    confirmation_hash = Column(Unicode)
    
    administrator_accounts = relation("Account", secondary=admins)
    member_accounts = relation("Account", secondary=members)
    
    def __init__(
            self, 
            username, 
            email_address, 
            password,
            first_name=None, 
            last_name=None, 
            time_zone=None, 
            github_username=None, 
            github_token=None,
            is_suspended=False, 
            has_confirmed=False, 
            confirmation_hash=None,
            administrator_accounts=None,
            member_accounts=None
        ):
        self.username = username
        self.email_address = email_address
        self.password = password
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name
        if time_zone:
            self.time_zone = time_zone
        if github_username:
            self.github_username = github_username
        if github_token:
            self.github_token = github_token
        self.is_suspended = is_suspended
        self.has_confirmed = has_confirmed
        if confirmation_hash:
            self.confirmation_hash = confirmation_hash
        if administrator_accounts:
            self.administrator_accounts = administrator_accounts
        if member_accounts:
            self.member_accounts = member_accounts
        
    
    
    def __repr__(self):
        return "<User('%s')>" % self.username
    
    
    @property
    def accounts(self):
        return self.administrator_accounts + self.member_accounts
        
    
    

class Account(SQLModel):
    """
    """
    
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, nullable=False)
    
    slug = Column(Unicode, unique=True)
    display_name = Column(Unicode)
    
    # 'basic', 'plus', 'premium', 'max'
    plan = Column(Unicode, default='basic')
    
    administrators = relation("User", secondary=admins)
    members = relation("User", secondary=members)
    
    def __init__(
            self, slug, display_name=None, plan='basic',
            administrators=None, members=None
        ):
        self.slug = slug
        if display_name:
            self.display_name = display_name
        self.plan = plan
        if administrators:
            self.administrators = administrators
        if members:
            self.members = members
        
    
    
    def __repr__(self):
        return "<Account('%s')>" % self.slug
    
    


SQLModel.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

### we use couchdb for the documents within an account

from couchdbkit import Server, ResourceNotFound, ResourceConflict
from couchdbkit import Document as CouchDocument
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema.properties import *

from github2.request import GithubError

import config
import utils

class Couch(object):
    """
    """
    
    def sync(self):
        path = join_path(dirname(__file__), '_design')
        self.loader = FileSystemDocsLoader(path)
        self.loader.sync(self.db)
        
    
    
    def __init__(self, sync=sys.platform == 'darwin'):
        self.db = Server().get_or_create_db('thruflo')
        if sync:
            self.sync()
        
    
    

couch = Couch()

class BaseDocument(CouchDocument):
    """Fixes.
    """
    
    @classmethod
    def get_or_create(cls, docid=None, db=None, dynamic_properties=True, **params):
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
            obj = cls()
            obj.update(params)
            obj.save()
            return obj
            
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
        """Convienience method for setting multiple properties.
        """
        
        for k, v in data.iteritems():
            setattr(self, k, v)
            
        
    
    

class AccountDocument(BaseDocument):
    """Extends.
    """
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    account_id = IntegerProperty(required=True)
    archived = BooleanProperty(default=False)
    

BaseDocument.set_db(couch.db)

class Blob(BaseDocument):
    """Uses a hash of repo/:branch/:path as id.
    """
    
    repo = StringProperty(required=True)
    branch = StringProperty(required=True)
    path = StringProperty(required=True)
    
    latest_commit = StringProperty()
    data = StringProperty()
    
    @classmethod
    def get_or_create_from(cls, repo, branch, path):
        s = '/'.join([repo, branch, path])
        docid = 'blob%s' % utils.generate_hash(s=s)
        return cls.get_or_create(
            docid=docid, 
            repo=repo,
            branch=branch, 
            path=path
        )
    
    
    def get_data(self, github):
        """This is where the magic happens.
          
          1.  ``Document`` lists ``:repo/:branch/:path``s
          2.  ``Blob`` has ``repo/:branch/:path as id``, ``latest commit`` and ``data``
          3.  in ``handle_commit`` (either via update hook, or against a commit list) we find all Blobs where ``latest commit`` matches a ``commit parent id``, set the ``latest commit`` to be the latest commit and clear the ``data``
          4.  When a document renders it goes:
              => bulk_get blobs
              => for blob in blobs: if not data: get data [if not latest commit, get latest commit]
          5.  When a blob is dropped on document:
              => get or create blob
              => if not data: get data [if not latest commit, get latest commit]
          
          
        """
        
        if not self.data:
            logging.debug('no data')
            if not self.latest_commit:
                logging.debug('no commit')
                try:
                    commits = github.commits.list(
                        self.repo,
                        self.branch,
                        file=self.path
                    )
                except GithubError, err:
                    logging.error(err)
                    raise NotImplementedError('@@ handle this!')
                self.latest_commit = commits[0].id
            try:
                blob = github.get_blob_info(
                    self.repo, 
                    self.latest_commit, 
                    self.path
                )
            except GithubError, err:
                logging.error(err)
                raise NotImplementedError('@@ handle this!')
            self.data = blob['data']
            if not self.data:
                self.data = ' ' # empty but evals to True
            self.save()
        return self.data
    
    

class SluggedDocument(AccountDocument):
    """Couchdb ``doc._id``s are long ``uuid4``s which is great
      for avoiding conflicts but too long to feature nicely in
      a user friendly URL.
      
      Equally, there's no reason we need to ask users to provide
      a slug when creating something.
      
      So, we need a mechanism to generate shorter, more user 
      friendly identifiers that can be used as the value of the 
      an instance's ``slug`` property.  
      
      Whilst we check when generating a slug that it's unique,
      they need to be fairly  unique, so it's very rare they 
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
    def get_from_slug(cls, account_id, slug):
        docs = cls.view(
            'all/type_slug_mod',
            startkey=[account_id, cls._doc_type, slug, None],
            endkey=[account_id, cls._doc_type, slug, []],
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
    def get_unique_slug(cls, account_id, max_tries=5):
        i = 1
        while True:
            if i > max_tries:
                raise Exception('Can\'t generate unique slug')
            else:
                slug = cls.generate_slug()
                if not cls.get_from_slug(account_id, slug):
                    break
                else:
                    i += 1
        return slug
        
    
    
    slug = StringProperty(required=True)
    

class Repository(AccountDocument):
    """
    """
    
    name = StringProperty(required=True)
    owner = StringProperty(required=True)
    url = StringProperty(required=True)
    description = StringProperty()
    
    branches = DictProperty()
    blob_tree = DictProperty()
    
    branch_paths = DictProperty()
    
    def update_branches(self, github):
        """repos/show/:user/:repo/branches
        """
        
        project = '%s/%s' % (self.owner, self.name)
        self.branches = github.repos.branches(project)
        return self.branches
        
    
    def update_blobs(self, github, branch):
        """tree/show/:user/:repo/:branch
          
          We parse::
          
              {
                  "foo.md": "#...",
                  "screenshots/photo.png": "#...",
                  "screenshots/foo/error.png": "#..."
              }
          
          Into::
            
              {
                  'f': {'foo.md': 'foo.md'},
                  'fs: {
                      'screenshots': {
                          'f': {'photo.png', 'screenshots/photo.png'},
                          'fs: {
                              'foo': {
                                  'f': {'error.png': 'screenshots/foo/error.png'}
                              }
                          }
                      }
                  }
              }
          
          
        """
        
        tree_sha = self.branches[branch]
        project = '%s/%s' % (self.owner, self.name)
        tree = github.request.get("blob/all", project, tree_sha).get('blobs')
        
        for k, v in tree.items():
            if not config.markdown_or_media.match(k):
                tree.pop(k)
        
        # first save the paths -- used to validate blob inserts against
        # could be removed if we bothered to write a couch view to unpack
        # self.blob_tree
        self.branch_paths[branch] = tree.keys()
        
        d = {'f': {}, 'fs': {}}
        blobs = copy.deepcopy(d)
        for item in tree:
            parts = item.split('/')
            # make sure the path exists in the dict structure
            context = blobs
            for k in parts[:-1]:
                if not context['fs'].has_key(k):
                    context['fs'][k] = copy.deepcopy(d)
                context = context['fs'][k]
            # insert / overwrite file
            context['f'][parts[-1]] = item
        
        self.blob_tree[branch] = blobs
        return self.blob_tree[branch]
        
    
    

class Document(SluggedDocument):
    """
    """
    
    display_name = StringProperty()
    stylesheet = StringProperty()
    
    blobs = StringListProperty()
    
    def get_blobs(self):
        logging.debug(self.blobs)
        return Blob.view(
            '_all_docs', 
            keys=self.blobs,
            include_docs=True
        ).all()
        
    
    

class Stylesheet(SluggedDocument):
    """
    """
    
    source = StringProperty()
    content = StringProperty()
    

