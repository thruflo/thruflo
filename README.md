
# thruflo

thruflo is a document authoring system.  It's still in early, alpha development probably won't work yet if you try to [use it][].


## Problem

* copying and pasting is inefficient
* formating is inefficient and introduces brand inconsistencies
* collaboration by email / locking is limited


## Solution

* write using markdown
* format using stylesheets
* reuse sections of previous documents


## Implementation

* web UI as editor
* don't think just type
* output
  * documents
  * presentations
  * webpages
  * slideshows
  * emailshots
  * to print
* formats:
  * pdf
  * html


## Reuse

* use markdown headings to demarcate sections
* sections stored using `<!-- section:${path} -->` comment syntax
* path is human readable, corresponding to `./path/fo/file.md#heading` (so it's manually editable by advanced users)
* section data is denormalised, with the locally cached (i.e.: in the file) version used if the section path fails to resolve

foo.md:

    # Foo
    
    ## Intro
    
    Lorum ipsum.
    
    ## Outro
    
    Dolores dulcit.

bar.md:

    # Bar
    
    <!-- section:foo.md#intro -->
    
    ## Intro
    
    Lorum ipsum.
    
    <!-- end section -->
    
    ## Outro
    
    Glug glug.


## Unpinning

* in the web UI, re-used sections are visually demarcated using [bespin syntax highlighting][]
* the heading is not editable
* editing the content saves the original document
* "unpin" to edit without saving the original (or to edit the heading)
* this removes the <!-- section --><!-- end section --> wrapper and just edits the new document directly

[use it]: http://github.com/thruflo/thruflo/blob/master/INSTALL.md
[bespin syntax highlighting]: https://bespin.mozillalabs.com/docs/pluginguide/syntax.html
