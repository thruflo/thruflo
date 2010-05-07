#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""We use a relational database for users and accounts and couchdb_
  (via Couchdbkit_) for the per-account document data.
  
  .. _couchdb: http://couchdb.apache.org/
  .. _Couchdbkit: http://couchdbkit.org/
"""

__all__ = [
    'db', 'User', 'Account', 'couch',
    'Template', 'Document', 'Topic',
    'Project', 'ProjectSection',
    'Deliverable', 'DeliverableSection'
]

import datetime
import logging
import re
import sys

from os.path import dirname, join as join_path

### patch database bindings so they don't block

#import gevent
#from gevent import monkey
#monkey.patch_all()

### we use a relational database for ``User``s and ``Account``s

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import Float, Integer, Unicode, Boolean, DateTime, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation

if sys.platform == 'darwin': # use sqlite in development
    engine = create_engine('sqlite:////env/thruflo/var/dev.db', echo=True)
else: # use postgresql in production
    import prod
    engine = create_engine(
        'postgresql+pg8000://%s:%s@%s/%s' % (
            prod.username,
            prod.password,
            prod.host,
            prod.dbname
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
    company = Column(Unicode)
    time_zone = Column(Integer)
    
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
            company=None, 
            time_zone=None, 
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
        if company:
            self.company = company
        if time_zone:
            self.time_zone = time_zone
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

from couchdbkit import Document, Server, ResourceNotFound, ResourceConflict
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema.properties import *

from fv_email import Email as EmailValidator
from utils import generate_hash

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

class CouchDBModel(Document):
    """Extensions to the couchdbkit base class.
    """
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    account_id = IntegerProperty(required=True)
    
    def __getattr__(self, key):
        """We like using ``doc.id``.
        """
        
        if key == 'id':
            key = '_id'
        return super(CouchDBModel, self).__getattr__(key)
        
    
    
    def update(self, data):
        """Convienience method for setting multiple properties.
        """
        
        for k, v in data.iteritems():
            setattr(self, k, v)
            
        
    
    


class Template(CouchDBModel):
    """
    """
    
    content = StringProperty()
    

Template.set_db(couch.db)

class Document(CouchDBModel):
    """
    """
    
    parts = StringListProperty()
    

Document.set_db(couch.db)

class Project(CouchDBModel):
    """
    """
    
    slug = StringProperty(required=True)
    display_name = StringProperty()
    

Project.set_db(couch.db)

class ProjectSection(CouchDBModel):
    """
    """
    
    project_id = StringProperty(required=True)
    section_type = StringProperty(required=True)
    branch_name = StringProperty(default=u'master')
    content = StringProperty()
    

ProjectSection.set_db(couch.db)

class Theme(CouchDBModel):
    """"""
    
    slug = StringProperty(required=True)
    display_name = StringProperty(required=True)
    
    content = StringProperty()
    

Theme.set_db(couch.db)

class Deliverable(CouchDBModel):
    """
    """
    
    slug = StringProperty(required=True)
    display_name = StringProperty()
    

Deliverable.set_db(couch.db)

class DeliverableSection(CouchDBModel):
    """
    """
    
    project_id = StringProperty(required=True)
    section_type = StringProperty(required=True)
    content = StringProperty()
    

DeliverableSection.set_db(couch.db)

def main():
    """Sync the couch db views.
    """
    
    couchdbs.sync()


if __name__ == '__main__':
    main()

