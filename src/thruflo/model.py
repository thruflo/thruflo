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
import os
import re
import sys
import uuid

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

from couchdbkit import Server, ResourceNotFound, ResourceConflict
from couchdbkit import Document as CouchDocument
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

class BaseDocument(CouchDocument):
    """Extends the couchdbkit base class.
    """
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    account_id = IntegerProperty(required=True)
    archived = BooleanProperty(default=False)
    
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
            
        
    
    

BaseDocument.set_db(couch.db)

class Container(BaseDocument):
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
            startkey=[account_id, cls._doc_type, slug, False],
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
    display_name = StringProperty()
    

class Contained(Container):
    """
    """
    
    parent_id = StringProperty(required=True)
    


document_types = [
    #'proposal', 
    'presentation', 
    #'release', 
    #'post'
]
section_type_mapping = [
    # 'executive_summary',
    # 'introduction',
    # 'about',
    {'casestudies': ['projects']}, 
    {'brief': ['projects']}
    # 'context',
    # 'approach',
    # 'implementation',
    # 'conclusion'
]
section_types = [item.keys()[0] for item in section_type_mapping]
unit_types = [
    'generic',
    'image', 
    'casestudy',
    # 'quote',
    # ...
]
class Document(Container):
    """We output ``Document``s, which contain a list of
      ``DocumentSection``s.
    """
    
    document_type = StringProperty(required=True, choices=document_types)
    
    sections = StringListProperty()
    

class Section(Contained):
    """``Section``s are boxes to put ``Unit``s in.
    """
    
    section_type = StringProperty(required=True, choices=section_types)
    
    units = StringListProperty()
    

class Unit(Contained):
    """...
      
      Each ``Template`` has a number of fields to map content to.  
      This is stored in ``slots``, where the field id is mapped to 
      the content ala::
          
          slots[field_id] = {
              'doc_type': ,
              'slug': ,
              'branch': 
          }
      
    """
    
    document_type = StringProperty(required=True, choices=document_types)
    unit_type = StringProperty(required=True, choices=unit_types)
    
    @property
    def template_slug():
        return '%s%s' % (self.document_type, self.unit_type)
        
    
    
    slots = DictProperty()
    


class ContentContainer(Container):
    """
    """
    
    __types__ = NotImplemented
    

class ContentSection(Contained):
    """
    """
    
    section_type = NotImplemented # StringProperty(required=True, choices=__types__)
    branch_name = StringProperty(default=u'master')
    content = StringProperty()


class Company(ContentContainer):
    """
    """
    
    __types__ = [
        'about',
        'clients',
        'contact',
        'logo'
    ]
    

class CompanySection(ContentSection):
    """
    """
    
    section_type = StringProperty(required=True, choices=Company.__types__)
    


class Project(ContentContainer):
    """
    """
    
    __types__ = [
        'brief',
        'solution',
        'results',
        'images',
        'videos'
    ]
    

class ProjectSection(ContentSection):
    """
    """
    
    section_type = StringProperty(required=True, choices=Project.__types__)
    


class Theme(ContentContainer):
    """
    """
    

class Deliverable(ContentContainer):
    """
    """
    


class Template(BaseDocument):
    """
    """
    
    content = StringProperty()
    


def rebuild_templates():
    """Overwrite ``Template`` instance content.
    """
    
    import tmpl
    
    template_docid_mapping = {
        'text_and_image': 'df27151ca436d3919ca877913e19c972',
        # '': '4822a744f45b40616a645a0308107ba2',
        # '': 'a8a295cd0ed60d4b95e06a09e52f0926',
        # '': 'a2c0d9bc9d09513d7d1e023181c31600',
        # '': '8d34fa7a2321f24ea5ee27eecfbdb6b6',
        # '': '01101881b1c368493b98275547c0d253',
        # '': '45db8419948e69b89e3cfd9adca09433',
        # '': 'dc671de04917cf8b236a6b73e23ddad8'
    }
    
    docs = []
    
    layout_folder_path = join_path(dirname(__file__), 'templates', 'layouts')
    for file_name in os.listdir(layout_folder_path):
        k = file_name.split('.')[0]
        docid = template_docid_mapping.get(k, None)
        if docid:
            try:
                doc = Template.get(docid)
            except ResourceNotFound:
                doc = Template(
                    _id=docid,
                    slug=k,
                    display_name=k.replace('_', ' ').title().replace('And', '&')
                )
            content = tmpl.render_tmpl('layouts/%s' % file_name)
            doc.content = ''.join(line.strip() for line in content.split('\n'))
            docs.append(doc)
    
    Template.bulk_save(docs)
    


def main():
    """Sync the couch db views.
    """
    
    couchdbs.sync()


if __name__ == '__main__':
    main()

