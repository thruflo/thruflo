
* create accordion with drag drop boxes UI
* handle drop of a content object:
  * need a template per ``document-type:source-type``
  * need to map the content object to the template
* select document section with google reader keys

* need to persist the mapping
* edit content object section in place, with select branch, save and fork

* markdown validation

* add ``Company`` object with generic about & contact info
* add ``Person`` object with generic 
* add structured ``Product`` object with types that yield budget and timeline info after configuration

* provide archive functionality for all objects
* provide merge functionality for all content objects

* add quicklinks and latest activity to dashboard view

* Refactor the user & account stuff into an individual package and integrate with Spreedly


----

::

    """
      
      Document # "Large Blue City Inn Website Presentation"
        - type # proposal | presentation | release | post
        Section # "Case Studies"
          Mapping # "North Chase Case Study"
            - template # '
            - slots # {'title': ':doc_type/:slug/:branch', '': '...'}
          ...
        ...
      ...
      
      
    """

class Template(ContentDocument):

class Document(Container):
    type = OneOf(['proposal', 'presentation', 'release', 'post'])
    sections = StringListProperty()
    

class DocumentSection(Contained):
    mappings = StringListProperty()
    

class Mapping(Contained):
    type = OneOf(['about', 'clientlist', 'casestudy', 'quote', 'image', 'generic']) # ...
    slots = DictProperty()
    



class Project(BaseDocument):

class Theme(BaseDocument):

class Deliverable(BaseDocument):

class Section(ContentDocument):
    parent_id = StringProperty(required=True)
    section_type = StringProperty(required=True)
    branch_name = StringProperty(default=u'master')
    




