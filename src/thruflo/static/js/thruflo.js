(function ($) {
    
    String.prototype.startsWith = function (pattern) {
      return this.indexOf(pattern) === 0;
    };
    String.prototype.endsWith = function (pattern) {
      var d = this.length - pattern.length;
      return d >= 0 && this.lastIndexOf(pattern) === d;
    };
    
    var CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.split(''); 
    Math.uuid = function() {
      var chars = CHARS, 
          uuid = new Array(36), 
          rnd = 0, 
          r;
      for (var i = 0; i < 36; i++) {
        if (i==8 || i==13 ||  i==18 || i==23) {
          uuid[i] = '-';
        } 
        else if (i==14) {
          uuid[i] = '4';
        } 
        else {
          if (rnd <= 0x02) {
            rnd = 0x2000000 + (Math.random() * 0x1000000) | 0;
          }
          r = rnd & 0xf;
          rnd = rnd >> 4;
          uuid[i] = chars[(i == 19) ? (r & 0x3) | 0x8 : r];
        }
      }
      return uuid.join('');
    };
    
    var log = function (what) {
      try { 
        console.log(what); 
      }
      catch (err) {
        // pass
      }
    };
    
    var current_path = window.location.pathname;
    if (current_path.endsWith('/')) {
      current_path = current_path.slice(0, -1);
    };
    
    var intid = 1;
    var client_id = Math.uuid();
    
    var special_selector_char = /([:\.\*\~\'\!\(\)\%])/gm;
    var escape_selector = function (whole_match, first_match) {
      return '\\' + first_match;
    };
    String.prototype.makeSelectorSafe = function () {
      return this.replace(special_selector_char, escape_selector);
    };
    
    var showdown_converter = new Showdown.converter();
    
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
    var UpdateListener = Class.extend({
        'min': 100,
        'max': 16000,
        'multiplier': 1.5,
        'backoff': 1000,
        '_handle_success': function (data) {
          if (data) {
            var _id = data['_id'];
            // invalidate the cache by ``_id``
            var doc_cache = $('#editor').get(0).doc_cache;
            doc_cache.invalidate(_id);
            // update the listings appropriately
            var listings = $('#' + data['type'] + '-listings');
            var listings_manager = listings.get(0).listings_manager;
            if (data.action == 'changed') {
              listings_manager.insert(
                null, 
                _id, 
                data['title'], 
                data['mod']
              );
            }
            else if (data.action == 'deleted') {
              listings_manager.remove(
                null, 
                _id
              );
            }
          }
        },
        '_handle_complete': function (transport) {
          if (transport.status < 400) {
            this.backoff = this.min;
          }
          else {
            this.backoff = this.backoff * this.multiplier;
            if (this.backoff > this.max) {
              this.backoff = this.max;
            }
          }
          window.setTimeout(
            $.proxy(this, 'poll'), 
            this.backoff
          );
        },
        'poll': function () {
          $.ajax({
              'url': current_path + '/listen',
              'type': 'POST',
              'dataType': 'json',
              'data': {'client_id': client_id},
              'success': $.proxy(this, '_handle_success'),
              'complete': $.proxy(this, '_handle_complete')
            }
          );
        },
        'init': function () {
          this.poll();
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
        }
      }
    );
    var EditorManager = SingleContextBase.extend({
        '_handle': 'editor_manager',
        '_current_editor': null,
        '_editors': {},
        'open': function (data) {
          var has_id = !!(data && data.hasOwnProperty('_id'));
          var exists = !!(has_id && this._editors.hasOwnProperty(data['_id']));
          if (exists) {
            this.select(data['_id']);
          }
          else {
            var editor = new Editor(data);
            if (has_id) {
              this.register(data['_id'], editor);
            } 
          }
        },
        'get_current': function () {
          return this._current_editor;
        },
        'set_current': function (editor) {
          this._current_editor = editor;
        },
        'register': function (_id, editor) {
          this._editors[_id] = editor;
        },
        'unregister': function (_id) {
          delete this._editors[_id];
        },
        'select': function (_id) {
          var editor = this._editors[_id];
          log(editor);
          var i = editor._get_tabs_index();
          $('#editor .tabs').tabs('select', i);
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
                this.get_current().save();
                return false;
              },
              this
            )
          );
          $('.delete-document', this.context).click(
            $.proxy(
              function (event) { 
                this.get_current().delete_();
                return false;
              },
              this
            )
          );
          /*
          $(document).keyup(
            $.proxy(
              function (event) {
                log(event.keyCode);
              },
              this
            )
          );
          */
        }
      }
    );
    var ListingsManager = SingleContextBase.extend({
        '_handle': 'listings_manager',
        '_sort_by': 'title', // | mod
        '_current_preview': null,
        'listing_template': $.template(
          '<li id="listing-${id}" class="listing document-listing">\
            <span class="listing-title">\
              <a href="#${id}" title="${title}"\
                  thruflo:mod="${mod}">\
                ${title}\
              </a>\
            </span>\
            <ul id="sections:${id}" class="sections-list">\
            </ul>\
          </li>'
        ),
        'show_preview': function (preview_id) {
          var preview_selector = '#' + preview_id.makeSelectorSafe();
          if (self._current_preview) {
            self._current_preview.hide();
          }
          self._current_preview = $(preview_selector);
          self._current_preview.show();
        },
        'sort_by': function (what) {
          this._sort_by = what;
          this.sort();
        },
        'insert': function (context, _id, title, mod) {
          if (!context) {
            $('#listing-' + _id, this.context).remove();
            $(this.context).append(
              this.listing_template, {
                'id': _id,
                'title': title,
                'mod': mod
              }
            );
            context = $('#listing-' + _id, this.context).get(0);
          }
          var listing = new Listing(context, _id, title);
          this.sort();
        },
        'remove': function (context, _id) {
          if (!context) {
            context = $('#listing-' + _id, this.context).get(0);
          }
          $(context).remove();
          this.sort();
        },
        'sort': function () {
          $('.listing', this.context).tsort(
            "span.listing-title a", {
              'attr': this._sort_by == 'title' ? 'title' : 'thruflo.mod'
            }
          );
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
    var Editor = Class.extend({
        '_handle': 'editor',
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
          var title = thruflo.markdown.get_first_title(content);
          return title;
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
            $('#editor').get(0).editor_manager.set_current(this);
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
          this.tab.editor = this;
          this.panel.editor = this;
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
                  // register with the EditorManager
                  $('#editor').get(0).editor_manager.register(self._id, this);
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
            var self = this;
            var url = current_path + '/delete';
            var params = {'_id': this._id, '_rev': this._rev};
            $.ajax({
                'url': url,
                'type': 'POST',
                'dataType': 'json',
                'data': params,
                'success': $.proxy(this, 'close'),
                'error': function (transport) {
                  log('@@ delete failed');
                  log(transport.status);
                  log(transport.responseText);
                }
              }
            );
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
          if (this._id) {
            $('#editor').get(0).editor_manager.unregister(this._id);
          } 
          var i = $('li', $('#editor .tabs')).index(this.tab);
          $('#editor .tabs').tabs('remove', i);
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
        '_rendered': false,
        '_callbacks': [],
        '_section_template': $.template(
          '<li id="section-${path}" class="listing ${type}-listing closed">\
            <span class="section-title">\
              <a href="#${path}" title="${title}">${title}</a>\
            </span>\
            <ul id="sections:${path}" class="sections-list"></ul>\
          </li>'
        ),
        '_section_preview': $.template(
          '<li id="preview-${path}" class="preview ${type}-preview">\
            <h4 class="preview-title">${title}</h4>\
            <div class="preview-content">${content}</div>\
          </li>'
        ),
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
        '_get_type': function () {
          if (!this.hasOwnProperty('_type')) {
            var resource_listing = $(this.context).parents('.resource-listing').get(0);
            log('resource_listing id: ' + resource_listing.id);
            this._type = resource_listing.id.replace('-listings', '');
          }
          return this._type;
        },
        '_get_manager': function () {
          if (!this.hasOwnProperty('_manager')) {
            var listings = $('#' + this._get_type() + '-listings');
            this._manager = listings.get(0).listings_manager;
          }
          return this._manager;
        },
        '_render_sections': function () {
          this.recursively_render_sections(this.sections);
          $('.sections-list', this.context).eq(0).treeview();
        },
        'recursively_render_sections': function (sections) { /*
            
            this.sections = [[
                [repo_id, 0, "Example Sections", 0, null, 0, null, ...],
                "\u000a## Section One\u000a\u000aFoo bar ... Footer\u000a\u000ayes."
              ], [
                [repo_id, 0, "Example Sections", 0, "Section One", 0, "Sub Section", ...]
                "u000aYes\u000a\u000a"
              ]
            ];
            
          */
          
          var i, 
              j, 
              l = sections.length,
              k = sections[0][0].length,
              section,
              title,
              key, 
              value, 
              children,
              key_item,
              path_items,
              parent_path,
              parent_id,
              path;
          
          for (i = 0; i < l; i++) { /*
              
              for each section
              
            */
            
            section = sections[i];
            key = section[0];
            value = section[1];
            children = section[2];
            
            /*
              
              get the path, e.g.:
              
                  /${docid}/Example%20Sections
                  /${docid}/Example%20Sections/Sections%20One/Sub%20Section
              
            */
            
            path_items = [];
            for (j = 2; j < k; j += 2) {
              key_item = key[j];
              if (key_item != null) {
                path_items.push(encodeURIComponent(key_item));
              }
              else {
                break;
              }
            }
            
            path = this._id + ':' + path_items.join(':');
            title = decodeURIComponent(path_items.pop());
            
            parent_path = this._id + ':' + path_items.join(':');
            if (parent_path.endsWith(':')) {
              parent_path = parent_path.slice(0, -1);
            }
            parent_id = 'sections:' + parent_path;
            parent_id = parent_id.makeSelectorSafe()
            
            // insert the section markup
            
            $('#' + parent_id).append(
              this._section_template, {
                'path': path,
                'type': this._get_type(),
                'title': title,
              }
            );
            
            // insert the showdown'd section content into a div
            
            $('#' + this._get_type() + '-previews').append(
              this._section_preview, {
                'path': path,
                'type': this._get_type(),
                'title': title,
                'content': showdown_converter.makeHtml(value)
              }
            );
            
            if (children.length) {
              this.recursively_render_sections(children.slice(0));
            }
            
          }
        },
        '_ensure_sections': function () {
          if (!this._rendered) {
            this._render_sections();
            $('span.section-title a', this.context).click($.proxy(this, 'select'));
            $('span.section-title a', this.context).dblclick($.proxy(this, 'open'));
            this._rendered = true;
          }
          log('@@ show sections');
        },
        '_trigger_open': function () {
          $('#editor').get(0).editor_manager.open(this.doc);
        },
        'init': function (context, _id, title) {
          this.doc = null;
          this.sections = null;
          this.context = context;
          this._id = _id;
          this.title = title;
          var link = $(this.context).find('a').first();
          link.click($.proxy(this, 'select'));
          link.dblclick($.proxy(this, 'open'));
        },
        'select': function (event) {
          var self = this;
          var target = $(event.target);
          this._ensure_has_doc(
            $.proxy(
              function () {
                this._ensure_sections();
                var ul = target.closest('ul');
                var li = target.closest('li');
                if (ul.hasClass('resource-listing')) {
                  ul = li.find('ul.sections-list').first();
                  li = ul.find('li.listing').first();
                  if (ul.hasClass('hidden')) {
                    ul.removeClass('hidden');
                    li.find('span').first().click();
                    if (!li.find('ul').first().is(':visible')) {
                      li.find('span').first().click();
                    }
                  }
                  else {
                    ul.addClass('hidden');
                  }
                }
                var preview_id = li.get(0).id.replace('section-', 'preview-');
                this._get_manager().show_preview(preview_id);
              },
              this
            )
          );
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
        
        var dc = new DocumentCache('#editor');
        
        /*
          
          manager for inserting and sorting listings
          
        */
        
        var dls = new ListingsManager('#document-listings');
        var ils = new ListingsManager('#image-listings');
        var vls = new ListingsManager('#video-listings');
        
        /*
          
          listen for updates
          
        */
        
        var ul = new UpdateListener();
        
        /*
          
          manager for adding and selecting documents
          
        */
        
        var em = new EditorManager('#editor');
        
        // don't think just type ;)
        em.open(null);
        
      }
    );
})(jQuery);
