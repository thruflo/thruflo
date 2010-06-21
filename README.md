
# thruflo


thruflo is a document authoring system.  It's still in early, alpha development and may well not work yet.


## Problem

* copying and pasting is inefficient
* formating is inefficient and introduces brand inconsistencies
* collaboration by email / locking is limited


## Solution

* write using markdown
* format using stylesheets
* reuse sections of previous documents


## Install

    git clone git@github.com:thruflo/thruflo.git
    cd thruflo


## Develop

    python setup.py develop


## Run

    ./bin/paster serve etc/dev.ini


## Output

* documents
* presentations
* webpages
* slideshows
* emailshots
* to print
* formats:
  * pdf
  * html


## Implementation

* users <-> repos many to many
* web UI with:
  * file browser / REST style UI to add / edit / delete documents
  * search UI to find and select sections to re-use
  * [bespin][]'d syntax highlighting / foo
* formats are views, where you apply a skin to the document


## Reuse Syntax

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

* in the web UI, re-used sections are visually demarcated
* the heading is not editable
* editing the content saves the original document
* "unpin" to edit without saving the original (or to edit the heading)
* this removes the <!-- section --><!-- end section --> wrapper and just edits the new document directly
