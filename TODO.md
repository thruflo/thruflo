
# 0.4

## Pinning

* unpin server side: when `section_id` doesn't resolve (refreshing dependency content)
* unpin client side: doubleclick to lose the `<!-- section -->` comments

## Demo Deploy

* deploy instance on linode
* minimal supervision / crontabbing for couch, redis & gunicorn
* make source private


# 0.5

## Save & close

* https://bespin.mozillalabs.com/docs/pluginguide/keymapping.html
  * ctlr+s to save
  * ctlr+shift+s to saveas
  * ctlr+w to close
  * ctlr+n for new
* when you save a document, you get a dialogue
  * the default suggestion is based on the lead H1
  + the title is 'suggestively normalised' lower() with funny chars removed & underscores
  + .md is auto added
  * you can select a folder
  * you can make a folder if it doesn't exist
  + uniqueness is enforced by using a hash of the path and filename as doc id
* prompt for save on `close` if changed
* on renaming, try to fix the affected section paths in docs depending on the renamed doc
* rerender sections if showing (render sections and click click down the tree)

## Sectioning

* handle first `# Heading` changing in the content after saved, inc from other doc

## Listing options

* search
* images & videos
* browse by folder
* sort


# 0.6

## Syntax Highlighting

* visually demarkate `<!-- section:... -->` comment blocks and section content

## Preview

* live document preview

## Generation

* generate template (i.e.: stylesheet) management
* views / selecting & publishing through stylesheets


# 0.7

## Merging

* handle conflicting updates with merging
* don't leave the user with a document they can't save (e.g.: prompt to force resolve merge conflict / overwrite / revert)

## user / access / subscription / pricing

* invite users to repos & manage who has access
* add any boilerplate around email confirmation, forgot pwd, etc.

## Payment / subscription

* sharing a repo requires paid subscription
* pricing plans based on no. of owned repos and no. users shared with


# 0.8

## Refactor

* refactor, document and test: try to simplify code and minimise bug potential
* rename any other "section" nomenclature that should use "dependency"
* sanity check logic in all parsing routines: make sure it's consistent and see if obvious bits of the js can be refactored
* build the design and the thruflo.markdown js from a single source
* explicitly resolve all the `@@`s
* stop and consider where the `shit should have thought of that before going live`s are going to come from: can we avoid any?

## Optimise

* some reasonable degree of db caching
* profile and optimise the slow bits, e.g.: sectioning
* thruflo.webapp etags
* ensure scripts, css and images are grouped and cached


# 0.9

## Prettify

* visual design
* skin
* document

## Analytics

* Google Analytics
* Crazy Egg

## SLA

* notifications, supervision, backups, redeployment, disaster recovery


# Onwards...

## Backwards compatibility

* pdf import
* word & powerpoint import

## Document export

* dump folders into zip
* version control back end

## Locking / Permissions

* locking files to author / specific users only
* more fine grained permissions on specific files / folders

## Versioning

* versioning / undo as per ([#][couchversioning]) 

## Editing

* copy and paste and insert from open document to open document


[couchversioning]: http://blog.couch.io/post/632718824/simple-document-versioning-with-couchdb
