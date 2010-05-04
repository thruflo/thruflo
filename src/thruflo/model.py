#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""We use a relational database for users and accounts and couchdb_
  (via Couchdbkit_) for the per-account document data.
  
  .. _couchdb: http://couchdb.apache.org/
  .. _Couchdbkit: http://couchdbkit.org/
"""

__all__ = [
    'db', 'User', 'Account', 'couchdbs',
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
            
        
    
    

class CouchDBModel(Model):
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
        
        docs_to_save = [
            doc._doc for doc in docs if doc._doc_type == cls._doc_type
        ]
        if not len(docs_to_save) == len(docs):
            raise ValueError(
                "one of your documents does not have the correct type"
            )
        
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
            logging.info(row)
            print row
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
            
        
    
    
    @classmethod
    def view(
            cls, 
            view_name,
            wrapper=None, 
            dynamic_properties=True,
            wrap_doc=True, 
            db=None,
            **params
        ):
        return cls.__view(
            view_type="view", 
            data=view_name, 
            wrapper=wrapper,
            dynamic_properties=dynamic_properties, 
            wrap_doc=wrap_doc,
            db=db,
            **params
        )
    
    
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
    
    _dbs = {}
    
    def __getitem__(self, db_name):
        if not self._dbs.has_key(db_name):
            self._dbs[db_name] = self.server.get_or_create_db(db_name)
        return self._dbs[db_name]
        
    
    
    def _sync_db(self, db_name):
        db = self[db_name]
        self.loader.sync(db)
        
    
    def sync(self, db_name=None):
        if not db_name:
            for db_name in self.server.all_dbs():
                self._sync_db(db_name)
        else:
            self._sync_db(db_name)
        
    
    
    def __init__(self, sync=False):
        path = join_path(dirname(__file__), '_design')
        self.loader = FileSystemDocsLoader(path)
        self.server = Server()
        if sys.platform == 'darwin':
            self.sync()
        
    
    

couchdbs = CouchDBs()

class Template(CouchDBModel):
    """
    """
    
    content = StringProperty()
    

class Document(CouchDBModel):
    """
    """
    
    parts = StringListProperty()
    


project_section_types = [
    'brief', 'solution', 'results'
]
class Project(CouchDBModel):
    """
    """
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    

class ProjectSection(CouchDBModel):
    """
    """
    
    project_id = SlugProperty(required=True)
    section_type = StringProperty(
        required=True, 
        choices=project_section_types
    )
    content = StringProperty()
    


class Theme(CouchDBModel):
    """"""
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    
    content = StringProperty()
    


deliverable_section_types = [
    'budget', 'process', 'time'
]
class Deliverable(CouchDBModel):
    """
    """
    
    slug = SlugProperty(required=True)
    display_name = StringProperty()
    

class DeliverableSection(CouchDBModel):
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
    
    couchdbs.sync()


if __name__ == '__main__':
    main()

