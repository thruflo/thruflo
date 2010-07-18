
# 0.4

## Reuse Sections

+ dummy hack the save dialogue:
  + normalise leading H1 lower() with funny chars removed & underscores & .md added as filename
  + uniqueness is enforced by using a hash of the path and filename as doc id

+ comment syntax: `<!-- section:/test_doc_one.md#Test Doc One##Sub Head pos:0:0 -->` where:
  + all the parts are `decodeURIComponent`ed with `/` and `#` escaped as `\/` and `\#`
  + `pos 0:0:1` is appended to provide the section order info

* what happens when:
  * fetch document:
    + with the latest content of each section
    + and latest rev data for each section
    * updating the section content and rev
    + and re-saving the document before returning it
  * render document
    * extract the rev from the section comment and hold it in memory against the section path
    * generate a hash of each section, to determin `changed` against
  * update from remote change
    * if the document is open, has the section changed? if not prompt the user to accept an update
    * if it has, flag the change to the user and either overwrite (@@ later merge) or unpin
    * update the rev in memory against the section as necessary
  * save
    + client side: send a dict of `rev` and `changed` flags along with the doc
    + server side: for each changed section, save that doc using the latest rev
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

