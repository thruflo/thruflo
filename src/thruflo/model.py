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
    'Blob'
]

import copy
import datetime
import logging
import os
import re
import sys
import uuid

from os.path import dirname, join as join_path

from couchdbkit import Server, ResourceNotFound, ResourceConflict
from couchdbkit import Document as CouchDBKitDocument
from couchdbkit.exceptions import BulkSaveError
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.schema import properties

import utils

# patterns to match the files we're interested in
markdown_or_media = re.compile(
    r'.*(\.md$)|(.png$)|(.jpg$)|(.jpeg$)|(.mp4$)', 
    re.U
)
stylesheet = re.compile(r'.*(\.css$)', re.U)

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

class BaseDocument(CouchDBKitDocument):
    """Tweak Couchdbkit a little and extends it to provide ``ver``
      ``mod`` and ``archived``.
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
        """Convienience method for setting multiple properties.
        """
        
        for k, v in data.iteritems():
            setattr(self, k, v)
            
        
    
    
    ver = IntegerProperty(default=1)
    mod = DateTimeProperty(auto_now=True)
    
    archived = BooleanProperty(default=False)
    

BaseDocument.set_db(couch.db)

class User(BaseDocument):
    """Github provides::
      
          {
            "user":{
              "plan":{
                "name":"small",
                "collaborators":5,
                "space":1228800,
                "private_repos":10
                },
              "gravatar_id":"b5c8346eb3ea83594fc97cb3cc4e44f5",
              "name":"James Arthur",
              "company":null,
              "location":"London, UK",
              "created_at":"2009/03/04 01:00:31 -0800",
              "disk_usage":57624,
              "collaborators":0,
              "public_repo_count":7,
              "public_gist_count":33,
              "blog":"http://www.thruflo.com",
              "following_count":5,
              "id":60015,
              "owned_private_repo_count":5,
              "private_gist_count":4,
              "total_private_repo_count":5,
              "followers_count":12,
              "login":"thruflo",
              "email":"thruflo@googlemail.com"
            }
          }
      
      Plus we store a list of repositories, their subscription level
      and their subscription expire time.
    """
    
    name = properties.StringProperty(required=True)
    login = properties.StringProperty(required=True)
    email = properties.StringProperty(required=True)
    
    location = properties.StringProperty()
    gravatar_id = properties.StringProperty()
    
    repositories = properties.StringListProperty()
    
    subscription_level = properties.StringProperty()
    subscription_expires = properties.StringProperty()
    

class Repository(BaseDocument):
    """
    """
    
    name = StringProperty(required=True)
    owner = StringProperty(required=True)
    url = StringProperty(required=True)
    description = StringProperty()
    
    branches = DictProperty()
    blob_tree = DictProperty()
    
    branch_paths = DictProperty()
    
    handled_commits = DictProperty()
    latest_sanity_checked_commits = DictProperty()
    
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
        
    
    def invalidate_blobs_content(self, user, commit, before=None):
        """Invalidate the content cache by deleting all Blobs 
          where ``latest commit`` matches a ``commit parent id``.
          
          Returns ``True`` if successful and ``False`` if there
          was a bulk save error.
        """
        
        logging.info('invalidating from')
        logging.info(commit)
        
        commit_ids = []
        if before:
            commit_ids.append(before)
        if commit.has_key('parents'):
            for item in commit.get('parents'):
                parent_id = item.get('id', None)
                if parent_id:
                    commit_ids.append(parent_id)
            
        logging.info('commit_ids')
        logging.info(commit_ids)
        
        blobs = Blob.view(
            'blob/latest_commit', 
            keys=commit_ids, 
            include_docs=True
        ).all()
        
        logging.info('blobs')
        logging.info(blobs)
        
        if len(blobs):
            logging.info('invalidating blobs')
            for blob in blobs:
                logging.info('blob: %s' % blob.id)
                blob.latest_commit = ''
                blob.data = ''
                logging.info(blob.to_json())
            try:
                Blob.get_db().bulk_save([blob.to_json() for blob in blobs])
            except BulkSaveError, err:
                logging.warning(err)
                return False
        
        logging.info('saved blobs')
        return True
        
    
    
    def update_commits(self, user, branch):
        """Check these against the full commits list, fetching and then
          handling any we missed since we last sanity checked.
        """
        
        username = user.github_username
        token = user.github_token
        github = Github(username=username, api_token=token)
        
        command = '/'.join(['commits', 'list', self.owner, self.name, branch])
        commits = github.request.make_request(command).get('commits')
        
        latest = None
        to_handle = []
        for item in commits:
            item_id = item.get('id')
            if item_id == self.latest_sanity_checked_commits.get(branch, None):
                logging.debug('matched that latest commit')
                break
            else:
                if latest is None:
                    latest = item_id
                    logging.debug('latest is %s' % latest)
                if not item_id in self.handled_commits.get(branch, []):
                    to_handle.append(item)
            
        if len(to_handle):
            self.handle_commits(user, branch, to_handle)
        
        if latest is not None:
            self.latest_sanity_checked_commits[branch] = latest
        
        self.handled_commits[branch] = []
        
    
    def handle_commits(self, user, branch, commits, before=None):
        """
        """
        
        logging.info('** invalidating commits **')
        logging.info('branch: %s' % branch)
        
        for item in commits:
            self.invalidate_blobs_content(user, item, before=before)
        
        bothered = True
        try:
            for commit in commits:
                logging.debug(commit)
                for k in ['added', 'modified', 'removed']:
                    if commit.has_key(k):
                        bothered = False
                        for item in commit[k]:
                            if config.markdown_or_media.match(item):
                                bothered = True
                                raise StopIteration
        except StopIteration:
            pass
        
        logging.info('bothered? %s' % bothered)
        
        if bothered:
            username = user.github_username
            token = user.github_token
            github = Github(username=username, api_token=token)
            logging.warning('@@ brute force update_blobs is not v. efficient')
            self.update_branches(github)
            self.update_blobs(github, branch)
            logging.info('@@ not doing any redis blocking pop foo *yet*')
        
        handled_commits = self.handled_commits.get(branch, [])
        for item in commits:
            handled_commits.append(item.get('id'))
        self.handled_commits[branch] = handled_commits
        
        logging.info('self.handled_commits')
        logging.info(self.handled_commits)
        
    
    

class Document(BaseDocument):
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
    def get_from_slug(cls, namespace, slug):
        docs = cls.view(
            'all/type_slug_mod',
            startkey=[namespace, cls._doc_type, slug, None],
            endkey=[namespace, cls._doc_type, slug, []],
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
        
    
    
    slug = StringProperty(required=True)
    
    display_name = StringProperty()
    
    blobs = StringListProperty()
    
    def get_blobs(self, github, force_update=True):
        """
        """
        
        blobs = Blob.view(
            '_all_docs', 
            keys=self.blobs,
            include_docs=True
        ).all()
        
        if force_update:
            to_save = {}
            for item in blobs:
                # if it's been updated once, use the updated version
                if to_save.has_key(item.id):
                    item = to_save.get(item.id)
                elif item.update_data(github, save=False):
                    to_save[item.id] = item
            if to_save:
                dicts = [item.to_json() for item in to_save.values()]
                Blob.get_db().bulk_save(dicts)
            
        return blobs
        
    
    
    # stylesheets = StringListProperty()
    

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
        
    
    
    def update_data(self, github, save=True):
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
        
        changed = False
        
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
            if save:
                self.save()
            changed = True
        
        return changed
        
    
    
    def get_data(self, github):
        self.update_data(github)
        return self.data
        
    
    


def sync():
    couch.sync()
    

