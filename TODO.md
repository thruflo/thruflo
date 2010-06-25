* implement the core document js class interface:
  * `init`: 
    + render core elements, inc. tabs bits and bespin editor
    + apply event handling
  * `save`, `saveas` and `move`:
    * we want "don't think just type"
    * naming and renaming done by *editing the top level heading*
    * if save without a heading, prompt for a heading and *write into the markdown*
    * how to handle overwriting?
    * https://bespin.mozillalabs.com/docs/pluginguide/keymapping.html
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
