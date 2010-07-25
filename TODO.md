
# 0.4

## Reuse Sections

* doubleclick to lose the `<!-- section -->` comments
* syntax highlighting to visually demarkate `<!-- section:... -->` comment blocks

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

## N.b.

* `_design/document/dependencies` should emit rows for start and end position
* `_design/document/sections` should emit rows for start and end position
* in `refresh_dependencies` get the positions using the view
* in `update_dependencies` get the positions using the view
* rename any other "section" nomenclature that should use "dependency"
* build the design and the thruflo.markdown js from a single source
* change the client side 'get start and end' logic to use the same as per the _design views


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

