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
import re
import sys
import uuid

from os.path import dirname, join as join_path

from couchdbkit import Server, ResourceNotFound, ResourceConflict
from couchdbkit import Document as CouchDBKitDocument
from couchdbkit.exceptions import BulkSaveError
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema.properties import *

from thruflo.webapp.utils import generate_hash

ten_lists = [
    [], [], [], [], [], [], [], [], [], []
]
ten_lies = [
    False, False, False, False, False, 
    False, False, False, False, False
]

SAFE_HASH = r'__thruflo::hash::thruflo__'
SAFE_FWDSLASH = r'__thruflo::fwdslash::thruflo__'

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
        
    
    
    def __init__(self, dbname='thruflo', settings={}):
        self.server = Server()
        self.db = self.server.get_or_create_db(dbname)
        self.app_settings = settings
        
    
    


class BaseDocument(CouchDBKitDocument):
    """Tweak Couchdbkit a little and extends it to provide ``ver``
      ``mod`` and ``archived``.
    """
    
    @classmethod
    def soft_get(cls, docid, rev=None, default=None):
        """Allows::
          
              inst = cls.soft_get(possible_id)
              if not inst: 
                  # possible_id didn't exist
              
          
        """
        
        try:
            return cls.get(docid, rev=rev)
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
    
    def list_documents(self, sort_by='filename', start=False, end=[], limit=2000):
        return Document.view(
            'document/by_%s' % sort_by,
            startkey=[self.id, start],
            endkey=[self.id, end],
            limit=limit
            # n.b.: no include_docs...
        ).all()
        
    
    

class Document(BaseDocument):
    """``Repository``s contain ``Document``s.
    """
    
    repository = StringProperty(required=True)
    path = StringProperty(required=True)
    filename = StringProperty(required=True)
    
    content = StringProperty()
    dependency_revs = DictProperty()
    
    @classmethod
    def get_docid(cls, section_id):
        path, filename = cls.extract_path_and_filename(section_id)
        return cls.generate_id(path=path, filename=filename)
        
    
    @classmethod
    def get_docid_or_sections_key(cls, repo_id, section_id):
        path, filename = cls.extract_path_and_filename(section_id)
        section_path = section_id.split(filename)[1]
        if not section_path:
            return cls.generate_id(path=path, filename=filename)
        else:
            key = [
                repo_id, path, filename,
                0, None, 
                0, None, 
                0, None, 
                0, None, 
                0, None, 
                0, None
            ]
            section_path = section_path.replace(r'\#', SAFE_HASH)
            section_path = section_path.replace(r'\/', SAFE_FWDSLASH)
            ordstring = section_path[section_path.index('ord:') + 4:]
            ords = [int(item) for item in ordstring.split(':')]
            level = 1
            hashes = '#'
            while True:
                ord_pos = 1 + (level * 2)
                text_pos = 2 + (level * 2)
                try:
                    s = section_path.index(hashes) + len(hashes)
                except ValueError:
                    break;
                else:
                    hashes += '#'
                    try:
                        e = section_path.index(hashes)
                    except ValueError:
                        e = section_path.index('ord:') - 1
                    text = section_path[s:e].replace(SAFE_HASH, r'#')
                    text = text.replace(SAFE_FWDSLASH, r'/')
                    key[ord_pos] = ords[level - 1]
                    key[text_pos] = text
                    level += 1
            return key
        
    
    @classmethod
    def extract_path_and_filename(cls, section_id):
        path_and_filename = section_id.split('.md#')[0]
        if not path_and_filename.endswith('.md'):
            path_and_filename = u'%s.md' % path_and_filename
        if not path_and_filename.startswith('/'):
            path_and_filename = u'/%s' % path_and_filename
        parts = path_and_filename.split('/')
        path = u'/%s' % u'/'.join(parts[0:-1])
        filename = parts[-1]
        return path, filename
        
    
    @classmethod
    def get_from_section_id(cls, section_id, rev=None):
        path, filename = cls.extract_path_and_filename(section_id)
        docid = cls.generate_id(path=path, filename=filename)
        return cls.soft_get(docid, rev=rev)
        
    
    @classmethod
    def generate_id(cls, path=None, filename=None):
        if path is None or filename is None:
            raise ValueError('must provide a path and filename to generate_id')
        s = u'%s/%s' % (path, filename)
        return generate_hash(s=s)
        
    
    @classmethod
    def get_heading_from_section_key(cls, section_key):
        """From::
          
              [
                u'c18862966c9a294c0f4ed6558a63540b', 
                u'/', 
                u'test_doc_one.md', 
                0, 
                u'Test Doc One', 
                0, 
                u'Sub Head', 
                0, 
                None, 
                0, 
                None, 
                0, 
                None, 
                0, 
                None
              ]
          
          To ``u'## Sub Head'``.
          
        """
        
        hashes = u'######'
        c = 6
        
        while True:
            i = 2 + (c * 2)
            if section_key[i] is None:
                c -= 1
                if c < 1:
                    return None
            else:
                return u'%s %s' % (hashes[:c], section_key[i])
            
        
    
    
    def _overwrite_content_at(self, startpos, endpos, new_content):
        """@@ todo, optimise this...
        """
        
        logging.warning('@@ todo: optimise _overwrite_content_at')
        
        self.content = u''.join([
                self.content[:startpos].rstrip() + 
                u'\n\n',
                new_content,
                u'\n\n',
                self.content[endpos:].lstrip()
            ]
        )
        
    
    
    def refresh_dependencies(self, should_save=True):
        """Goes this like:
          
          * get the reused section_ids from the doc's content
          * do a keys lookup to check which dependencies have changed
          * for those that have:
            * lookup the latest corresponding content for the stored doc
            * @@ todo: it it doesn't exist unpin
            * if it's changed, update the relevant section of content
              and return the rev to go with the id
            
          
        """
        
        # @@ todo: optimise
        logging.warning('*** @@ fetching *every* dependency *every* fetch ***')
        logging.warning('*** could do with some caching at some point ***')
        
        if should_save:
            snapshot = self.content
        
        # get the reused section_ids and corresponding content
        dependencies = couch.db.view(
            'document/dependencies', 
            startkey=[self.repository, self.id, False],
            endkey=[self.repository, self.id, []]
        ).all()
        
        # weed out duplicates
        deduplicated = []
        section_ids = {}
        for item in dependencies:
            section_id = item['key'][4]
            if not section_id in section_ids:
                section_ids[section_id] = True
                deduplicated.append(item)
            
        # weed out unchanged
        maybe_changed = []
        query_keys = []
        for item in deduplicated:
            section_id = item['key'][4]
            if self.dependency_revs.has_key(section_id):
                docid = self.get_docid(item['key'][4])
                query_keys.append([docid, self.dependency_revs.get(section_id)])
            else:
                query_keys.append([None, None])
        
        results = couch.db.view('document/by_rev', keys=query_keys)
        result_ids = [item.get('id') for item in results]
        
        for item in deduplicated:
            if not item.get('id') in result_ids:
                maybe_changed.append(item)
            
        for item in maybe_changed:
            section_id = item['key'][4]
            docid_or_section_key = Document.get_docid_or_sections_key(
                self.repository, 
                section_id
            )
            doc = None
            actual_content = None
            if isinstance(docid_or_section_key, basestring):
                docid = docid_or_section_key
                doc = Document.soft_get(docid)
                if doc is not None:
                    actual_content = doc.content
            else:
                section_key = docid_or_section_key
                section = couch.db.view('document/sections', key=section_key).first()
                if section is not None:
                    doc = Document.get(section['id'])
                    if doc is not None:
                        actual_content = u'%s\n\n%s' % (
                            self.get_heading_from_section_key(section_key),
                            section['value'].strip()
                        )
            if actual_content is None:
                logging.warning('*** @@ section_id doesn\'t resolve ***')
                logging.warning('*** need to handle this by unpinning ***')
            else: # update the relevant section of content
                self.dependency_revs[section_id] = doc._rev
                self.overwrite_dependency_content(section_id, actual_content)
            
        if should_save and not self.content == snapshot:
            self.save()
        
    
    def overwrite_dependency_content(self, section_id, section_content):
        """Like ``overwrite_section_content`` below, but finds the dependency 
          content as demarked by the ``<!-- section:... --> ... 
          <!-- end section:... -->`` comments and overwrites the content.
        """
        
        section_content = section_content.strip()
        start_comment = re.compile(
            r'<!-- section:' + re.escape(section_id) + r' -->',
            re.M | re.U
        )
        all_comments = re.compile(
            r' section:' + re.escape(section_id) + r' -->',
            re.M | re.U
        )
        start_scan_pos = 0
        # iterate through the content to handle all the instances 
        # of this dependency
        while True:
            # find the start comment
            match = start_comment.search(self.content, start_scan_pos)
            if not match: 
                # if we don't find one, then exit
                break;
            # find the corresponding end comment (n.b.: nested dependencies get
            # overwritten...)
            startpos = match.end()
            endpos = -1
            match_number = 0
            scan_pos = startpos
            while True:
                match = all_comments.search(self.content, scan_pos)
                if not match:
                    start_scan_pos = startpos + 1
                    break;
                if self.content[match.start() - 3:match.start()] == 'end':
                    # it's an end comment
                    if match_number == 0:
                        # we have the corresponding end comment
                        endpos = match.start() - 9
                        break;
                    else:
                        # we're one match closer
                        match_number -= 1
                else:
                    # we're one match further away
                    match_number += 1
                scan_pos = match.end()
            if endpos < 0:
                break;
            match_length = match.end() - match.start()
            start_scan_pos = startpos + len(section_content) + match_length
            self._overwrite_content_at(startpos, endpos, section_content)
        
    
    def overwrite_section_content(self, section_id, section_content):
        """Update the part of the ``content`` of this ``Document``s, as 
          identified by the ``section_id``, ala::
          
              path/foo/filename.md#Heading##Sub Head###Sub Sub Head ord:0:0:0
          
          The ``section_path`` we're interested in this bit::
          
              #Heading##Sub Head###Sub Sub Head ord:0:0:0
          
          The process is then to use this path to identify the start and
          end pos of the relevant chunk of content in this doc and to overwrite
          it with the ``section_content`` provided.
          
        """
        
        section_path = u'.md'.join(section_id.split(u'.md')[1:])
        
        if not section_path:
            self.content = u'\n%s\n' % section_content
            return
        
        section_path = section_path.replace(r'\#', SAFE_HASH)
        section_path = section_path.replace(r'\/', SAFE_FWDSLASH)
        
        ordstring = section_path[section_path.index('ord:') + 4:]
        ords = [int(item) for item in ordstring.split(':')]
        
        startpos = -1
        level = 1
        hashes = '#'
        
        # for each level
        while True:
            # get the text, e.g.: ``Test Doc One``
            try:
                s = section_path.index(hashes) + len(hashes)
            except ValueError:
                # when we're out of sections,
                # set the endpos to either the start of 
                # the next sibling heading or the end of doc
                setext_pattern = None
                if level == 2:
                    setext_pattern = r'^(.+?)[ \t]*\n=+[ \t]*[\n|$]'
                elif level == 3:
                    setext_pattern = r'^(.+?)[ \t]*\n-+[ \t]*[\n|$]'
                atx_pattern = r''.join([
                        r'^\#{1,',
                        str(level - 1),
                        r'}[ \t]*(?!\#)(.+?)[ \t]*(?<!\\)\#*[\n|$]'
                    ]
                )
                if setext_pattern:
                    sibling_or_end_of_doc = re.compile(
                        r'(' + atx_pattern + r')|(' + setext_pattern + r')',
                        re.U | re.M
                    )
                else:
                    sibling_or_end_of_doc = re.compile(atx_pattern, re.U | re.M)
                sibling_match = sibling_or_end_of_doc.search(self.content, startpos + 1)
                endpos = sibling_match and sibling_match.start() or -1
                break;
            else:
                hashes += '#'
                try:
                    e = section_path.index(hashes)
                except ValueError:
                    e = section_path.index('ord:') - 1
                text = section_path[s:e].replace(SAFE_HASH, r'#')
                text = text.replace(SAFE_FWDSLASH, r'/')
                
                atx_pattern = r''.join([
                        r'^\#{',
                        str(level),
                        r'}[ \t]*(',
                        re.escape(text),
                        r')[ \t]*(?<!\\)\#*[\n|$]'
                    ]
                )
                if level < 3:
                    if level == 1:
                        setext_pattern = r''.join([
                                r'^(',
                                re.escape(text),
                                r')[ \t]*\n=+[ \t]*[\n|$]'
                            ]
                        )
                    elif level == 2:
                        setext_pattern = r''.join([
                                r'^(',
                                re.escape(text),
                                r')[ \t]*\n-+[ \t]*[\n|$]'
                            ]
                        )
                    target_heading = re.compile(
                        r'(' + atx_pattern + r')|(' + setext_pattern + r')', 
                        re.U | re.M
                    )
                else:
                    target_heading = re.compile(atx_pattern, re.U | re.M)
                target_match_number = ords[level - 1] / 2
                match_number = 0
                # loop through, matching via setext or atx from pos
                while True:
                    match = target_heading.search(self.content, startpos)
                    last_heading = match.groups()[0]
                    if not match:
                        break;
                    else:
                        # if this is the n'th match where n = ord/2
                        startpos = match.end()
                        if match_number == target_match_number:
                            # startpos = the end of the heading
                            break;
                        match_number += 1
                level += 1
            
        if startpos > -1:
            # remove the ##Heading from the section content
            section_content = u''.join(section_content.split(last_heading)[1:])
            # overwrite the content
            self._overwrite_content_at(startpos, endpos, section_content.strip())
            
        
    
    def update_dependencies(self, sections):
        """Updates other documents' section content.
        """
        
        logging.warning(
          '@@ update_dependencies needs to take care over fetching and saving'
        )
        logging.warning(
          '@@ update_dependencies needs to handle ResourceConflict'
        )
        
        changed_docs = []
        revs = {}
        
        for data in sections:
            section_id = data.get('id')
            # if we've not processed this before
            if not section_id in revs:
                # get the doc that contains this section
                kwargs = {}
                if data.has_key('rev'):
                    kwargs['rev'] = data['rev']
                # @@ this should be bulk & handled...
                doc = Document.get_from_section_id(section_id, **kwargs)
                if doc is not None:
                    # if its changed
                    has_changed = data.get('changed', True)
                    if has_changed:
                        # amend its content and try to save it 
                        doc.overwrite_section_content(section_id, data['content'])
                        # @@ this should be bulk & handled...
                        doc.save()
                        changed_docs.append(doc)
                    # either way, grab the doc._rev for this section_id
                    revs[section_id] = doc._rev
                
        # store the revs
        self.dependency_revs = revs
        
        # returned a list of changed docs and the dict of revs
        return changed_docs, revs
        
    
    


def couch_factory(settings):
    """Returns a ``Couch`` instance.  
      
      Written to be used within the context of an app factory,
      so that the model classes can be aware of the application 
      settings, ala:
          
          import model
          
          def app_factory(global_config, **local_conf):
              settings = global_config
              # ... etc.
              
              model.couch = model.couch_factory(settings)
              
          
      The couch instance provides:
      
      * `couch.server`: low level server interface
      * `couch.db`: the database this app is using
      * `couch.app_settings`: the application settings
      * `coucn.sync()` to sync the couchdb views in the 
        database with the ``./_design`` folder.
      
    """
    
    # instantiate
    couch = Couch(settings=settings)
    
    # in dev mode always sync the views
    if settings['dev_mode']:
        couch.sync()
    
    # tell all the ``Document`` classes to use
    # ``couch.db``
    BaseDocument.set_db(couch.db)
    
    # return
    return couch
    

def sync():
    """Syncs the couchdb views in the database with the 
      ``./_design`` folder.
    """
    
    couch = Couch()
    couch.sync()
    

