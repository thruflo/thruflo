This is a `document generation system <http://cl.o.se/post/561413499/business-development-with-version-control>`_ in progress.  I'm having a play with it on a prototype level, so I'd suggest you don't use it.

central insights
----------------

* reuse
* branching & merging
* microsyntax

sliderocket
-----------

* reuse (comprehensive, very lowest common consumer)

Where's the space?

* more automation: master prototype
* markdown: github approach

Where's the product?

* web interface, defined structure = web service product
* github -> less obvious

Is there a middle way?

* conventions::

    ./projects/:project
    [*.md|images|videos|subsection/...and repeat...

Qu: is github a good way to manage blob data (no)

* sliderocket style image selection from a gallery through a web UI
* expose the rendering on a standalone service?
* interesting to think what this would be
* distractions of the impl!  yawsgif...

Qu: what are the fundamentals of a standalone rendering service?

* markdown
* stylesheet

Qu: can you seperate the aspects into small units?

* rendering service
* content management service [possibly using git covention approach?]
* document generation UI (?)

Qu: if managing through textmate, how do you trigger & view?  that document fine tuning...

Qu: what are the issues wth the structured through the web approach?

* documents -> sections -> units -> slots might look like::

    Document
      - title, etc.
      Section
        - title, etc.
        Unit
          - type [becomes css selector]
          Slot
            - content object path
          ...
        ...
      ...
    ...

So to generate, imagine all this is stored in a Document class except the content is looked up::

    doc = self.context
    for section in doc:
      for unit in section:
        for slot in unit:
          value = model.get(content_object)
        
      
    

Qu: can we simplify ``Unit``s and ``Slot``s?

Imagine 'content' is just any markdown document, with no structure pre-defined, what then?

* you can't map it to slots (there are no fields / properties)
* you can just render it

So it becomes::

    doc = self.context
    for section in doc:
      for unit in section:
        value = model.get(content_object)
      
    

Now imagine we have::

    ./projects/
      openIDEO/
        brief.md
        solution.md
        images/
          image1.png
          image2.jpg
        videos/
          screencast.mp4
      ...
    ./company/
      about.md
      clients.md
    

These could be grouped into sections that were explicitly:

* Project specific
* Generic

But what about just losing Sections::

    def apply_unit(path):
        unit = repo.get(path)
        if unit.type == 'markdown':
            return unit
        elif unit.type == 'image':
            return wrap_image(unit)
        elif unit.type == 'video':
            return wrap_video(unit)
        
    
    doc = self.context
    for unit in doc:
      value = apply_doc(unit.repository_path)
      
    
What does this achieve?  Thing back to central insight:

* reuse
* branching & merging
* microsyntax

It gives you all three.  The only thing it doesn't give you is fancy slide formatting.