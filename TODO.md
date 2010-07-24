
# 0.4

## Reuse Sections

x rename `update_dependencies` to `refresh_dependencies`
x rename `save_sections` to `update_dependencies`
x store dependency_revs dict against a stored document
x couch view of `Document`s by [id, rev]
+ optimised `doc.overwrite_content_at(start, end, new_content)` method
x when `refresh`ing:
  x do a keys lookup to check which dependencies have changed
  x use overwrite_content_at
x `update_dependencies` should use `overwrite_content_at`
x pass ``session_id`` and ``originating_document_id`` through the changed machinery

* in `Editor.handle_document_changed`:
  * work out what's going on with `session_id` and `originating_document_id`
  * if this document id matches originating_document_id ignore
  * else:
    * `handle_content_changed`: if we've edited the content, prompt, else overwrite
    * `handle_dependency_changed`: if we've edited the section, prompt, else overwrite
    * check changed against the saved checksum!
  * fire some events to can be handled to tell the user what's going on

* seems listen isn't clearing the list (or we have ye-old redis keys about)

* doubleclick to lose the `<!-- section -->` comments
* syntax highlighting to visually demarkate `<!-- section:... -->` comment blocks

* `_design/document/dependencies` should emit rows for start and end position
* `_design/document/sections` should emit rows for start and end position
* in `refresh_dependencies` get the positions using the view
* in `update_dependencies` get the positions using the view
* rename any other "section" nomenclature that should use "dependency"
* build the design and the thruflo.markdown js from a single source
* change the client side 'get start and end' logic to use the same as per the _design views

## Preview

* live document preview


# 0.5

## Save & close

* https://bespin.mozillalabs.com/docs/pluginguide/keymapping.html
  * ctlr+s to save
  * ctlr+shift+s to saveas
  * ctlr+w to close
  * ctlr+n for new
* when you save a document, you get a dialogue
  * the default suggestion is based on the lead H1
  * the title is 'suggestively normalised' lower() with funny chars removed & underscores
  * .md is auto added
  * you can select a folder
  * you can make a folder if it doesn't exist
  * uniqueness is enforced by using a hash of the path and filename as doc id
* prompt for save on `close` if changed
* on renaming, try to fix the affected section paths in docs depending on the renamed doc
* rerender sections if showing (render sections and click click down the tree)

## Listing options

* search
* images & videos
* browse by folder
* sort


# 0.6

## Generation

* generate template (i.e.: stylesheet) management
* views / selecting & publishing through stylesheets


# 0.7

## refactor user / access / subscription / pricing

* invite users to repos & manage who has access

## Deployment

* deploy supervised
* v. minimal optimisation of db calls every request / server side sectioning
* thruflo.webapp etags


# 0.8

## Versioning

* versioning / undo as per ([#][couchversioning]) 

## Editing

* handle conflicting updates with merging
* copy and paste and insert from open document to open document


# 1.n

## Payment / subscription

* sharing a repo requires paid subscription
* pricing plans based on no. of owned repos and no. users shared with

## Backwards compatibility

* pdf import
* word & powerpoint import

## Document export

* dump folders into zip


[couchversioning]: http://blog.couch.io/post/632718824/simple-document-versioning-with-couchdb

