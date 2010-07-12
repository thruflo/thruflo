
# 0.4

## Drag to insert

* insert markup for:
  * document
  * document section
* insert into the right place

## Syntax highlighted UI

* sort out the trimming so it's consistent coming back from the db
* use bespin syntax highlighting to visually demarkate `<!-- section:... -->` comment blocks
  * write syntax highlighter plugin
  * `dryrun` rake / bundle a custom embedded bespin
  * apply styles and behaviour to bespin canvas elements
* `unpin`: 
  * click to lose the `<!-- section -->` comments and ensure the behaviour is removed

## Preview

* live document preview


# 0.5

## Save & close

* if save without a heading, prompt for a heading and *write into the markdown*
* saveas and move dialog with folders
* prompt for save on `close`
* rerender sections if showing (render sections and click click down the tree)
* handle conflicting saves


## Listing options

* images & videos
* search
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
* v. minimal optimisation of db calls every request
* thruflo.webapp etags


# 0.8

## Versioning

* versioning / undo as per ([#][couchversioning]) 

## Editing

* https://bespin.mozillalabs.com/docs/pluginguide/keymapping.html
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

