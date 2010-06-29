(function ($) {
    
    String.prototype.startsWith = function (pattern) {
      return this.indexOf(pattern) === 0;
    };
    String.prototype.endsWith = function (pattern) {
      var d = this.length - pattern.length;
      return d >= 0 && this.lastIndexOf(pattern) === d;
    };
    
    var log = function (what) {
      try { 
        console.log(what); 
      }
      catch (err) {
        // pass
      }
    };
    
    var intid = 1;
    var current_path = window.location.pathname;
    if (current_path.endsWith('/')) {
      current_path = current_path.slice(0, -1);
    };
    
    var SingleContextBase = Class.extend({
        '_handle': null,
        'init': function (context_id) {
          this.context = $(context_id).get(0);
          this.context[this._handle] = this;
        }
      }
    );
    var SelectedBase = Class.extend({
        '_handle': null,
        'init': function (selector) {
          var self = this;
          this.contexts = $(selector);
          this.contexts.each(
            function () {
              this[self._handle] = self;
            }
          );
        }
      }
    );
    var DocumentCache = SingleContextBase.extend({
        '_handle': 'doc_cache',
        '_docs': {},
        '_doc_methods': {
          'get_sections': function () {
            if (!this.hasOwnProperty('_sections')) {
              this._sections = thruflo.markdown.get_sections(this);
            }
            return this._sections;
          }
        },
        'get_document': function (_id, callback, args) {
          if (!this._docs.hasOwnProperty(_id)) {
            var _handle_success = function (data) {
              this._docs[_id] = $.extend(data['doc'], this._doc_methods);
              callback(this._docs[_id], args);
            };
            var _handle_error = function (transport) {
              log('@@ fetch failed');
              log(transport.responseText);
              callback(null, args);
            };
            $.ajax({
                'url': current_path + '/fetch',
                'type': 'POST',
                'dataType': 'json',
                'data': {'_id': _id},
                'success': $.proxy(_handle_success, this),
                'error': $.proxy(_handle_error, this)
              }
            );
          }
          else {
            callback(this._docs[_id], args);
          }
        },
        'invalidate': function (_id) {
          return delete this._docs[_id];
        },
        'init': function (context_id) {
          this._super(context_id);
          
          log('@@ doc cache should poll for updates & invalidate when changed');
          
        }
      }
    );
    var DocumentManager = SingleContextBase.extend({
        '_handle': 'doc_manager',
        '_current_document': null,
        'open': function (data) {
          
          var d = new DocumentEditor(data);
          
          // @@
          
          
        },
        'get_current_document': function () {
          return this._current_document;
        },
        'set_current_document': function (document_instance) {
          this._current_document = document_instance;
        },
        'init': function (context_id) {
          this._super(context_id);
          $('.add-new-document-link', this.context).click(
            $.proxy(
              function (event) { 
                this.open(null); 
                return false;
              },
              this
            )
          );
          $('.save-document', this.context).click(
            $.proxy(
              function (event) { 
                this.get_current_document.save();
                return false;
              },
              this
            )
          );
          $('.delete-document', this.context).click(
            $.proxy(
              function (event) { 
                this.get_current_document.delete_();
                return false;
              },
              this
            )
          );
          $(document).keyup(
            $.proxy(
              function (event) {
                log(event.keyCode);
              },
              this
            )
          );
        }
      }
    );
    var ListingsManager = SingleContextBase.extend({
        '_handle': 'listings_manager',
        'insert': function (context, _id, title) {
          
          var listing = new Listing(context, _id, title);
          
          // @@ ...
          
          
        },
        'remove': function (_id) {
          
        },
        'sort': function (sort_by) {
          
        },
        'init': function (context_id) {
          this._super(context_id);
          var self = this;
          $('.listing', this.context).each(
            function () {
              var _id = this.id.split('listing-')[1];
              var title = $(this).find('a').eq(0).attr('title');
              self.insert(this, _id, title);
            }
          );
        }
      }
    );
    var DocumentEditor = Class.extend({
        '_handle': 'doc_editor',
        'UNTITLED': 'Untitled',
        '_generate_tabs_id': function () {
          var id = intid;
          intid += 1;
          return id;
        },
        '_get_tabs_index': function () {
          return $('li', $('#editor .tabs')).index(this.tab);
        },
        '_get_title': function (content) { /*
            
            Extracts document title from the opening H1
            in the markdown content.
            
            If the first non-whitespace in the document 
            content isn't a valid setext or atx H1 then
            returns null.
            
            
          */
          return thruflo.markdown.get_first_title(content);
        },
        '_trim_title': function (title) {
          if (title.length > 20) {
            title = title.slice(0, 16) + ' ...';
          }
          return title;
        },
        '_handle_bespin_load': function () {
          log('bespin loaded');
          // get a handle on the editor
          var doc = this.frame.contentWindow.document;
          this.bespin = $('#editor', doc).get(0).bespin;
          this.editor = this.bespin.editor;
          // default the content to something friendly
          this.editor.value = this.initial_content;
          this.editor.setLineNumber(4);
          this.editor.focus = true;
          // handle events
          this.editor.textChanged.add(this.handle_text_change);
          this.editor.selectionChanged.add(this.handle_selection_change);
        },
        '_handle_tab_selected': function (event, index) {
          log('thruflo:tab:selected: ' + index);
          if (index == this._get_tabs_index()) {
            if (typeof(this.editor) != 'undefined') {
              this.editor.focus = true;
            }
            $('#editor').get(0).doc_manager.set_current_document(this);
          }
        },
        'init': function (doc) {
          var id_no = this._generate_tabs_id();
          var tab_id = '#tabs-' + id_no;
          var t = $('#editor .tabs');
          if (doc) {
            this._id = doc._id;
            this._rev = doc._rev;
            this.path = doc.path;
            this.initial_content = doc.content;
            t.tabs('add', tab_id, this._trim_title(doc.title));
          }
          else {
            this._id = null;
            this._rev = null;
            this.path = '/';
            this.initial_content = '\n# ' + this.UNTITLED + ' ' + id_no + '\n\n\n';
            t.tabs('add', tab_id, this.UNTITLED + ' ' + id_no);
          }
          this.tab = $('li', t).last();
          this.panel = $(tab_id);
          this.frame = $('iframe', this.panel).get(0);
          // apply event handling
          this.frame.contentWindow.onBespinLoad = $.proxy(this, '_handle_bespin_load');
          $('.tab-button', this.tab).click(
            $.proxy(this, 'close')
          );
          $(document).bind(
            'thruflo:tab:selected', 
            $.proxy(this, '_handle_tab_selected')
          );
          // ensure we're now the current document
          $(document).trigger(
            'thruflo:tab:selected', [
              this._get_tabs_index()
            ]
          );
          // provide dom handles
          this.tab.doc_editor = this;
          this.panel.doc_editor = this;
        },
        'open': function () {},
        'save': function () {
          log('save: ' + this._get_tabs_index());
          var content = this.editor.value;
          var title = this._get_title(content);
          if (!title) {
            alert('please add a heading (@@ make nice prompt)');
          }
          else {
            var self = this;
            if (this._id && this._rev) {
              var url = current_path + '/overwrite';
              var params = {
                '_id': this._id,
                '_rev': this._rev,
                'title': title,
                'content': content,
                'path': this.path
              };
            }
            else {
              var url = current_path + '/create';
              var params = {
                'title': title,
                'content': content,
                'path': this.path
              };
            }
            log('_' + params.content + '_');
            $.ajax({
                'url': url,
                'type': 'POST',
                'dataType': 'json',
                'data': params,
                'success': function (data) {
                  // store the new doc data
                  self._id = data['_id'];
                  self._rev = data['_rev'];
                  // update the tab label
                  var label = self._trim_title(title);
                  self.tab.find('span').text(label);
                },
                'error': function (transport, text_status) {
                  log('@@ save failed');
                  log(transport.responseText);
                },
                'complete': function () {
                  self.editor.focus = true;
                }
              }
            );
          }
        },
        'move': function () {},
        'delete_': function () {
          if (!this._id && !this._rev) {
            this.close();
          }
          else {
            alert('@@ delete_...');
          }
        },
        'insert': function () {},
        'unpin': function () {},
        'preview': function () {},
        'validate': function () {},
        'expand': function () {},
        'collapse': function () {},
        'close': function () {
          log('@@ check not changed on close');
          var i = $('li', t).index(this.tab);
          t.tabs('remove', i);
        },
        'handle_text_change': function (oldRange, newRange, newText) {
          /*
            
            log('text changed');
            log(oldRange);
            log(newRange);
            log(newText);
            
            
          */
        },
        'handle_selection_change': function (newSelection) {
          /*
            
            log('selection changed');
            log(newSelection);
            
            
          */
        }
      }
    );
    var Listing = SingleContextBase.extend({
        '_handle': 'listing',
        '_fetching': false,
        '_callbacks': [],
        '_call_callbacks': function () { /*
            
            When you trigger a dblclick event in most browsers,
            you actually trigger:
            
                mousedown
                mouseup
                click
                mousedown
                mouseup
                click
                dblclick
            
            So, to hang ``click`` and a ``dblclick`` events off
            the same element, you need an idempotent, unobtrusive
            ``click`` handler that can be called twice without
            harm when dblclick is triggered.
            
            Now, because our click handler is wrapped by 
            ``this._ensure_has_doc``, which may make a ajax call,
            we have to invent this 'store up your callbacks and
            only make one ajax fetch' palava.
            
            In a nutshell:
            
            * we use a ``this._fetching`` to record whether an
              ajax call is in progress
            * if it is, we cache the callbacks in a list
            * when the request comes back, we call all the callbacks
              in order, clear the list and set ``this._fetching`` to
              false
            
            N.b.: this is infinitely better than some sort of nasty
            'delay all clicks by 300ms' hack, shudder.
            
          */
          for (var i = 0; i < this._callbacks.length; i++) {
            this._callbacks[i]();
          }
        },
        '_ensure_has_doc': function (callback) {
          this._callbacks.push(callback);
          if (!this._fetching) {
            $('#editor').get(0).doc_cache.get_document(
              this._id, 
              $.proxy(
                function (doc) {
                  if (doc) {
                    this.doc = doc;
                    this.sections = doc.get_sections();
                    this._call_callbacks();
                  }
                  this._callbacks = [];
                  this._fetching = false;
                },
                this
              )
            );
          }
        },
        '_render_sections': function () {
          log('@@ render sections');
          log(this.sections);
        },
        '_show_sections': function () {
          log('@@ show sections');
          log(this.sections);
        },
        '_trigger_open': function () {
          $('#editor').get(0).doc_manager.open(this.doc);
        },
        'init': function (context, _id, title) {
          this.doc = null;
          this.sections = null;
          this.context = context;
          this._id = _id;
          this.title = title;
          $(this.context).click($.proxy(this, 'select'));
          $(this.context).dblclick($.proxy(this, 'open'));
        },
        'select': function () {
          this._ensure_has_doc($.proxy(this, '_show_sections'));
        },
        'open': function () {
          this._ensure_has_doc($.proxy(this, '_trigger_open'));
        }
      }
    );
    
    $(document).ready(
      function () {
        
        /*
          
          we use a tab view for the document editors
          
        */
        
        $('#editor .tabs').tabs({
            'tabTemplate': '<li>\
              <a href="#{href}">\
                <span class="label">#{label}</span>\
              </a>\
              <div class="tab-button-container">\
                <a href="#close" class="tab-button close">[ x ]</a>\
                <a href="#changed" class="tab-button changed hidden">[ O ]</a>\
              </div>\
            </li>',
            'panelTemplate': '<div>\
              <iframe src="/bespin" width="572px" height="353px">\
              </iframe>\
            </div>',
            'add': function(event, ui) {
              $('#editor .tabs').tabs('select', '#' + ui.panel.id);
            },
            'select': function (event, ui) {
              var tab = $(ui.tab).parent();
              var i = $('li', $('#editor .tabs')).index(tab);
              $(document).trigger('thruflo:tab:selected', [i]);
            }
          }
        );
        
        /*
          
          an accordion for the different listings
          
        */
        
        $('#editor .accordion').accordion({
            'autoHeight': false,
            'collapsible': true
          }
        );
        
        /*
          
          we keep a cache of documents in the browser
          
        */
        
        var doc_cache = new DocumentCache('#editor');
        
        /*
          
          manager for adding and selecting documents
          
        */
        
        var doc_manager = new DocumentManager('#editor');
        
        /*
          
          manager for inserting and sorting listings
          
        */
        
        var doc_listings = new ListingsManager('#document-listings');
        // var img_listings = new ListingsManager('#image-listings');
        // var vid_listings = new ListingsManager('#video-listings');
        
        /*
          
          don't think just type ;)
          
        */
        
        doc_manager.open(null);
        
      }
    );
})(jQuery);
