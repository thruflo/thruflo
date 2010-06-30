
+ in the ``DocumentManager`` constructor, start long polling, 
  passing a ``client_id`` param to identify the browser

+ register that ``client_id`` against the repo in redis, so 
  it's renewed every poll and expires after a few minutes
  
+ when a document is updated on the server side, get all the
  ``client_id``s that are live against a repo and push the
  new / changed ``doc._id`` and ``doc.title`` to their queue

* in the client side poll ``success`` method, tell the 
  ``DocumentManager`` to invalidate the cache by ``_id``
  and tell the appropriate ``ListingsManager`` to remove
  the existing listing record for the ``_id`` and insert
  the new listing at the right point

>>> debug title = '#' in the db
>>> debug the listen success not being called

* click in the listings expands / contracts the treeview and scrolls the preview area

  * `delete`:
    * delete the document from the filesystem and close
  * `insert`:
    * insert markup for document / document section / image / video
    * insert into the right place
    * *use bespin syntax highlighting* to visually demarkate `<!-- section:... -->` comment blocks
      * write syntax highlighter plugin
      * `dryrun` rake / bundle a custom embedded bespin
    * apply styles and behaviour to bespin canvas elements added by syntax highlighting
  * `unpin`: 
    * lose the `<!-- section -->` comments and thus auto lose the behaviour added
  * `close`:
    + remove the UI elements
    * prompt for save?
* firefox tab style [ + ] button
* right hand side UI
  * accordion
  * list / tree / search
  * select
  * dblclick open
  * drag insert
  * upload / images / videos
* extend the markdown editor
  * if save without a heading, prompt for a heading and *write into the markdown*
  * https://bespin.mozillalabs.com/docs/pluginguide/keymapping.html
  * saveas and move dialog with folders
  * live document preview
  * validate
  * expand / collapse
* copy and paste and insert from open document to open document
* redis backed updates per repo with:

    `{'_id': updated_doc_id, '_src': some_sort_of_token_per_rendered_page}`

* handle conflicting saves
* template (i.e.: stylesheet) management
* views / selecting & publishing through stylesheets
* refactor user / access / subscription / pricing:
  * sharing a repo requires paid subscription
  * pricing plans based on no. of owned repos and no. users shared with
  * invite users to repos & manage who has access
* versioning / undo as per ([#][]) 
* etags

[#]: http://blog.couch.io/post/632718824/simple-document-versioning-with-couchdb
