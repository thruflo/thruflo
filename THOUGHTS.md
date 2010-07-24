
*n.b.: *these are just the author's collated ramblings, for the sake of recording them for possible future reference*


* idea for a markdown > pdf service
* somewhat opaquely recorded as [business development with version control][]
* essential, core insight was my own copy and pasting
* massively innefficient, so it's certain this is a good well to drill: there *must* be productivity gains

* however, the initial writeup involved version control
* so, not only do we start with "write docs in markdown"
* we also see immediately that markdown integrates with version control
* version control is the way developers avoid copy and paste

* we have a waterfall:
  * markdown enables:
    * faster editing (& all the other value of microsyntax)
    * templatability
    * version control, which enables:
      * collaboration
      * undo
  * reuse is enabled by spliting the whole down into parts (slides / sections / pages / etc.), this actually has nothing to do with markdown
* it is interesting that these two are *different and unrelated*
* *unless* the sectioning is implicit in the markdown

* now, through the web is shit but it's a bit better with bespin

* question is, what does it mean for the sectioning to be implicit in the markup?
* well, the principle of re-use is:
  * you can find what you've written before
  * you can include it in your current document
  * *iff* when you edit it *in either document* it updates both
* it's interesting to see that there's a lot of value in simple *findability* of sections which, of course, with a markdown-in-on-object-dbm or even in TextMate is dead easy
* however, if we want to impl that iff, then we need:
  * have some hook at the save level which intercepts changes and either:
    * actually saves the sections individually
    * or overwrites all of the documents

* what happens when you change the section title?
* this is a problem with "completely implict": they user must surely know what's going on? this could mean:
  * "prompt on save if issue"
  * or "explicitly fork or overwrite"

* the initial, core insight has been implemented, in one area by sliderocket
* you have various tools that take markdown and create docs, slideshows, etc.

* question is, what's to be done with this?  how should a system be integrated?

* UI approaches:
  * vanilla push to git w. document creation UI
  * edit through the web CMS style

* idealised system, with no care for the impl details:
  * user can add, edit, find, search, share, etc. documents and fragments of documents
  * templates can be setup either through a WYSIWYG or through stylesheets
  * 

* concept of business just using it for:
  * web
  * email
  * documents
  * presentations
  * email shots
  * business cards
* you can see that:
  * more and more works in the browser
  * some is syndicated
  * some needs to go through an emailshot / external APIs
  * some is printed via local network
  * some needs to be professionally printed
* all these are basically views, where you apply a skin to core markup

* definitely a question over whether you provide some sort of initial skeletal structure or just leave it up to the user to import
* task around backwards compatibility (e.g.: import word, import keynote...)
* question around edit in place

* **perhaps** there is an insight that we can use markdown # head ## ings to section documents?  i.e.: you just write the damn thing but then when you save it, the system automatically sections everything.  then, when you want to reuse, you point to it

* interesting to explore the potential editing UIs:
  * lightbox drag drop sections
  * search to grab sections by text (surely a very useful tool)

* it has to be explicit to a user what they are editing
* it has to be as simple as possible for a user to edit docs, i.e.: is through the web really the best user experience?
* if not through the web then what?  client dev appears preclusive.  ideally leverage existing editor habits but then how to package and potentially handle the sectionation?






* there is a super simple starting point:
  * write a document in markdown
  * publish it through a skin

* you then come along and you want to write another document
* this is largely new but includes bits of the previous document

* what are the options for how this could be implemented?
* you find the bit of the previous document you want to re-use and:
  * you copy it, period.
  * you:
    * include a reference to it
    * expose the ability to edit it through the new document's UI
    * save the original so both docs update
  * ...?
  
* if the second option, we've established that we need to make what's happening explicit to the user
* it may be reasonable to assume that only some parts of some docs will be re-used, so perhaps they are explicitly visually demarkated in the document flow, with a 'fork' option to 'unpin' them from their source, i.e.:
  * if a user chooses to go and find a section in a previous document and selects it, it's added to the new document "as" the source
  * they can then "unpin" it to just hack on it with no consequences
  * otherwise, changes are understood to want to apply to all
  * a "pinned" source *retains its structural elements*

question: what are the structural elements?  well they must be section headings so you have:
    
    # h1
    
    
    ## h2
    
    foobar
    
    ### h3
    
    foo
    
    ### h3 again
    
    bar
    
    
    ## h2 again
    
    barfoo
    
    ### h3
    
    bar
    
    ### h3 again
    
    foo
    
    
    # h1 again
    
    ...
    
    

so the *single structural element* is the toplevel heading by which the section is selected, e.g.: the second h3 in the first h2 of the first h1 would have `### h3 again` fixed.

so perhaps in the source you would have a doc like:
    
    ## h2
    
    foobar
    
    ### h3
    
    foo
    

say this then inserts a section from another document:

    ## h2
    
    foobar
    
    <!-- section:6785f...6f89 -->
    
    ### h3
    
    foo
    

that's the document source code looking decent enough in version control (n.b.: ) but what about these sections themselves?  do we need to store seperate files?  if so, how is that done in a git folder structure?

one approach might be to explicitly use a path as the id, e.g.:

    <!-- section:/usr/james/foo.md#heading_id -->

possibly using the [python-markdown HeaderId][] extension id creation syntax.  then what happens when the user goes back to the original document?

one solution would be that it is also "pinned", which preserves the heading and thus the heading_id.  this could then have a mechanism where if unpinned, the system found the next document in line containing that section and updated all references to it to use that document as the reference from now on.

however, what about the path, the `/usr/james/foo.md`?  this could have the same thing applied, i.e.: the file could be 'pinned'.  also, when using version control, you get information about what's happened to files in the commit.

but hang on, what are we trying to achieve here: if we're editing everything through the web, then presumably we can intercept this stuff?

actually the question above was: do we need to save sections as individual documents in an object database?  what are the forces?

* if we just use paths/ids that resolve to a part of a document, we'll need a method like `get_section(section_id)` to parse documents?  or perhaps we index documents by section on save?  plus, we'll need to perhaps implement `handle_section_unpin` and `handle_document_unpin` routines

the issue here actually comes down to: do we want to want to expose the git repo tree to raw editing?

* presumably there is an advantage to doing so: advanced users can just edit directly and push rather than go through the web
* but then perhaps this could be achieved by having the git repo and the object db as seperate, pushing completed documents to git repo but storing sections in, say, couch?

How about de-normalising the section content and wrapping it with a comment:

    ## h2
    
    foobar
    
    <!-- section:/usr/james/foo.md#heading_id -->
    
    ### h3 again
    
    bar
    
    <!-- end section -->
    
    ### h3
    
    foo
    

now if you edit the source code, you can:

1. see the master section, so go and edit that
2. remove the comment to 'unpin' and hack away

plus, if a path doesn't resolve, the document falls back on the cached content.

we provide a through the web interface with a custom js client that happens to use bespin's events to see what's going on (and presumably provides some sort of multi-bespined-textarea solution to the documents which reference sections, i.e.: each section has to have its own text area) and actually persist everything in a git repo.


[business development with version control]: http://cl.o.se/post/561413499/business-development-with-version-control

[python-markdown HeaderId]: http://www.freewisdom.org/projects/python-markdown/HeaderId










# what's going on


## server side

### Fetching

In `fetch`, `dependencies = doc.update_dependencies()` updates the content of the dependencies using the section to read the latest version

Currently, overwriting is done with Python parsing to determine where to insert: instead, the couch view that returns the section ids and content should also emit rows for start and end position.

Currently, the rev data isn't stored in the document.  If we write the rev into the section or even store a dict of dependency section ids and revs against the `Document` instance and index documents against rev, we can do a keys lookup to check which dependencies have changed when fetching.

N.b.: `update_dependencies` should be `refresh_dependencies`.

### Saving

In `create` and `overwrite`, `dependencies = doc.save_sections(params['sections'])`.  This takes a list of dependencies (called `sections`, sigh) and, for each of them, gets the corresponding document (using the path/filename.md to get the docid and the latest rev that the parent document knows about), calls `doc.update_section_content(section_id, data['content'])` for each of them.

As above, overwriting using Python parsing.  This needs to be done using a position index in the couch view that spits out the heading delimited sections.

N.b.: `save_sections` should be `update_dependencies`.

### Live Updates
  
Atm, `self._notify_doc_changed(changed)` sends a list of all the documents that have changed.  This is then picked up client side.  The document cache is invalidated and a document change event is fired, which `Editor`s handle.


## client side

### `Editor.handle_document_changed`

Atm, this parses the current `bespin_editor.value` for section_ids, and for those that match, overwrites the editor content *if it's not what's in the update dependency*.  If we do want to do this, the check needs to first be against *the checksum when the doc was last checked*.  i.e.: we want to overwrite if the user hasn't changed it and "merge" if they have.

Qu: do we actually want live updates?  What's the UX?  Let's think through the scenarios with a `Document` rendered into an `Editor`.  Well, if the originating session id is passed through and the originating editor (somehow) then we can provide an interface of:

* `handle_document_changed(session_id, originating_document_id)`
* `handle_dependency_changed(session_id, originating_document_id)`

This allows us to stub these methods for now, as per:

* `handle_document_changed`: if we've edited the document, prompt, else overwrite
* `handle_dependency_changed`: if we've edited the section, prompt, else overwrite

Both these approaches assume that *we want to update documents silently*.  This is fine as a stub.  We can add a UI later for accepting changes, or provide options to a user, etc.

### markdown

We need to replicate the logic that spits out the positioning by passing a flag to the methods.  It may be actually that we should generate the actual js files from a single source file.  This could apply a patch / use flags to control the different final output.

# bugs

* seems listen isn't clearing the list (or we have ye-old redis keys about)
