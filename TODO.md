
+ click on the listing gets and reveals the content & sections
* click in the listings expands / contracts the treeview and scrolls the preview area

* on save, need to insert the new document in the listings at the right point sorted by title / update the relevant listing instance

* document cache in the browser
* sectioning logic in the browser that precisely matches the view code
* redis backed updates per repo with:

    `{'_id': updated_doc_id, '_src': some_sort_of_token_per_rendered_page}`

* js classes have a routine to `_get_content` and / or `_get_sections` which goes via the document cache

  * `open`:
    * get raw content via AJAX
    * possibly register for update events?
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
* live updates
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
