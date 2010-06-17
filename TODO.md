* document editing UI, bespin, section re-use handling
  * new document / rename document:
    * we want "don't think just type"
    * so we need a save and rename dialog? yuck...
  * render document content
    * get raw content via AJAX
    * render within the right markup through the js client
    * parse `<!-- section:... -->` comments into seperate editors
    * pin / unpin
  * open document tabview
  * firefox tab style [ + ] button
  * markdown editor
    * save / flag changed / close
    * live document preview
    * validate
    * expand / collapse
  * insert sections
    * accordion
    * list / tree / search
    * select
    * dblclick open
    * drag insert
    * upload 
* template management
* views / selecting & publishing through stylesheets
* refactor user / access / subscription / pricing:
  * sharing a repo requires paid subscription
  * pricing plans based on no. of owned repos and no. users shared with
  * invite users to repos & manage who has access
* handle conflicting saves
* versioning / undo via http://blog.couch.io/post/632718824/simple-document-versioning-with-couchdb
