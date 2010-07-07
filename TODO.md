
* delete needs to clear the preview area
* save => makes new listing => click on it and and it dissapears
* can the listing state not be preserved through an update?
* the doubleclick show / hide flash is a bit village: maybe use fixclick for *just* the listing sections?
* editor._get_tabs_index is not a function
* double click on a listing isn't reliable: opens the wrong one

* bespin now supports multiple editors: strip out the iframe fandango

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
  * prompt for save?

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
* handle conflicting saves
* template (i.e.: stylesheet) management
* views / selecting & publishing through stylesheets
* refactor user / access / subscription / pricing:
  * sharing a repo requires paid subscription
  * pricing plans based on no. of owned repos and no. users shared with
  * invite users to repos & manage who has access
* versioning / undo as per ([#][]) 
* thruflo.webapp etags

[#]: http://blog.couch.io/post/632718824/simple-document-versioning-with-couchdb
