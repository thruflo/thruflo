(function ($) {
    
    String.prototype.startsWith = function (pattern) {
      return this.indexOf(pattern) === 0;
    };
    String.prototype.endsWith = function (pattern) {
      var d = this.length - pattern.length;
      return d >= 0 && this.lastIndexOf(pattern) === d;
    };
    
    var SAFE_HASH = '__thruflo::hash::thruflo__';
    var safe_hash_pattern = /\_\_thruflo\:\:hash\:\:thruflo\_\_/gm;
    var SAFE_FWDSLASH = '__thruflo::fwdslash::thruflo__';
    var safe_fwdslash_pattern = /\_\_thruflo\:\:fwdslash\:\:thruflo\_\_/gm;
    
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
        '_handle_success': function (items) {
          if (items) {
            for (var i = 0; i < items.length; i++) {
              var data = items[i];
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
                  data['filename'], 
                  data['mod']
                );
                $(document).trigger('document:changed', [data]);
              }
              else if (data.action == 'deleted') {
                listings_manager.remove(
                  null, 
                  _id
                );
                $(document).trigger('document:deleted', [data]);
              }
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
        '_fetching': {},
        '_callbacks': {},
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
            // store the callback against the id
            if (!this._callbacks.hasOwnProperty(_id)) {
              this._callbacks[_id] = [];
            }
            this._callbacks[_id].push(callback);
            // if we're not already fetching
            if (!this._fetching.hasOwnProperty(_id)) {
              // flag that we are fetching
              this._fetching[_id] = true;
              var _handle_success = function (data) {
                log('@@ fetch success'); log(data);
                this._docs[_id] = $.extend(
                  data['doc'], 
                  this._doc_methods, {
                    'dependencies': data.dependencies
                  }
                );
                var doc = this._docs[_id];
                for (var i = 0; i < this._callbacks[_id].length; i++) {
                  this._callbacks[_id][i](doc, args);
                }
              };
              var _handle_error = function (transport) {
                log('@@ fetch error'); log(transport.responseText);
                for (var i = 0; i < this._callbacks[_id].length; i++) {
                  this._callbacks[_id][i](null, args);
                }
              };
              var _handle_complete = function () {
                delete this._callbacks[_id];
                delete this._fetching[_id];
              };
              $.ajax({
                  'url': current_path + '/fetch',
                  'type': 'POST',
                  'dataType': 'json',
                  'data': {'_id': _id},
                  'success': $.proxy(_handle_success, this),
                  'error': $.proxy(_handle_error, this),
                  'complete': $.proxy(_handle_complete, this)
                }
              );
            }
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
        'get_current': function () {
          return this._current_editor;
        },
        'set_current': function (editor) {
          this._current_editor = editor;
        },
        'refresh_selected': function () {
          var t = $('#editor .tabs');
          t.tabs('select', t.tabs('option', 'selected'));
        },
        'register': function (editor_id, editor) {
          this._editors[editor_id] = editor;
        },
        'unregister': function (editor_id) {
          delete this._editors[editor_id];
        },
        'reregister': function (previous_id, new_id, editor) {
          var e = editor;
          this.unregister(previous_id);
          this.register(new_id, e);
        },
        'add_new': function (event) {
          if (event) { event.stopPropagation(); }
          
          // create markup
          
          var editor = new Editor();
          this.register(editor.id, editor);
          this.set_current(editor);
        },
        'save_current': function (event) {
          if (event) { event.stopPropagation(); }
          var target = this.get_current();
          if (target) {
            target.save();
          }
        },
        'delete_current': function (event) {
          if (event) { event.stopPropagation(); }
          var target = this.get_current();
          if (target) {
            var editor_id = target.id;
            target.delete_();
            this.set_current(null);
          }
        },
        'trigger_select': function (editor_id) {
          var editor = this._editors[editor_id];
          $(editor.tab).click();
        },
        'select': function (editor_id) {
          var editor = this._editors[editor_id];
          editor.focus();
          this.set_current(editor);
        },
        'open': function (data) {
          var has_id = !!(data && data.hasOwnProperty('_id'));
          var exists = !!(has_id && this._editors.hasOwnProperty(data['_id']));
          if (exists) {
            var editor_id = data['_id'];
            var editor = this._editors[editor_id];
            this.trigger_select(editor_id);
            editor.update(data);
          }
          else {
            var editor = new Editor(data);
            this.register(editor.id, editor);
            this.set_current(editor);
          }
        },
        'init': function (context_id) {
          this._super(context_id);
          $('.add-new-document', this.context).click($.proxy(this, 'add_new'));
          $('.save-document', this.context).click($.proxy(this, 'save_current'));
          $('.delete-document', this.context).click($.proxy(this, 'delete_current'));
          // don't think just type ;)
          this.add_new();
        }
      }
    );
    var Editor = Class.extend({
        '_handle': 'editor',
        '_section_revs': {},
        '_section_hashes': {},
        'UNTITLED': 'Untitled',
        '_generate_tabs_id': function () {
          var id = intid;
          intid += 1;
          return id;
        },
        '_normalise_title': function (title) {
          log('@@ dummy hack normalising title');
          return $.trim(
            title.toLowerCase().replace(
              /[-\s]/g, '_'
            ).replace(
              /[^\w]/g, ''
            )
          ) + '.md';
        },
        '_get_filename': function (content) { /*
            
            Extracts document title from the opening H1
            in the markdown content.
            
            If the first non-whitespace in the document 
            content isn't a valid setext or atx H1 then
            returns null.
            
            
          */
          var title = thruflo.markdown.get_first_title(content);
          return this._normalise_title(title);
        },
        '_trim_title': function (title) {
          if (title.length > 20) {
            title = title.slice(0, 16) + ' ...';
          }
          return title;
        },
        '_extract_path_and_filename': function(section_id) {
          var path_and_filename = section_id.split('.md#')[0];
          if (!path_and_filename.endsWith('.md')) {
            path_and_filename = path_and_filename + '.md';
          }
          if (!path_and_filename.startsWith('/')) {
            path_and_filename = '/' + path_and_filename;
          }
          log(path_and_filename);
          var parts = path_and_filename.split('/');
          var path = '/' + parts.slice(0, -1).join('/');
          var filename = parts.pop();
          return [path, filename];
        },
        '_get_docid_or_sections_key': function (repo_id, doc_id, section_id) {
          log('get_docid_or_sections_key: ' + section_id);
          
          var path_and_filename = this._extract_path_and_filename(section_id);
          var path = path_and_filename[0];
          var filename = path_and_filename[1];
          
          var section_path = section_id.split(filename)[1];
          if (!section_path) {
            return doc_id;
          }
          else {
            var key = [
              repo_id, 
              path, 
              filename,
              0, null, 
              0, null, 
              0, null, 
              0, null, 
              0, null, 
              0, null
            ];
            section_path = section_path.replace(/\#/gm, SAFE_HASH);
            section_path = section_path.replace(/\//gm, SAFE_FWDSLASH);
            var ordstring = section_path.slice(section_path.indexOf('ord:') + 4);
            var ordparts = ordstring.split(':');
            var ords = [];
            for (var i = 0; i < ordparts.length; i++) {
              ords[i] = parseInt(ordparts[i]);
            }
            var level = 1
            var hashes = '#'
            while (true) {
              var ord_pos = 1 + (level * 2);
              var text_pos = 2 + (level * 2);
              try {
                var s = section_path.indexOf(hashes) + hashes.length;
              }
              catch (e) {
                break;
              }
              hashes += '#';
              try {
                var e = section_path.indexOf(hashes);
              }
              catch (e) {
                var e = section_path.index('ord:') - 1;
              }
              var text = section_path.substr(s, e).replace(safe_hash_pattern, '#');
              text = text.replace(safe_fwdslash_pattern, '/');
              key[ord_pos] = ords[level - 1];
              key[text_pos] = text;
              level += 1;
            }
            return key;
          }
        },
        '_generate_section_id': function (path, filename, section_path, sections) { /*
            
            We want `path/filename.md#Heading##Sub Heading` where all the parts 
            are `decodeURIComponent`ed with `/` and `#` escaped.
            
            We need the numbers from the section path to uniquely identify the
            sections, e.g.: `0:Test%20Doc%20One:0:Sub%20Head`.  So we compromise
            and append them so the output is like:
            
            path/My File.md#Test Doc One##Sub Head###Sub Sub Head 0:0:2
            
          */
          
          var i, 
              part, 
              parts = [path, filename].concat(section_path.split(':')),
              l = parts.length;
          // decode and escape
          for (i = 2; i < l; i++) {
            part = decodeURIComponent(parts[i]);
            parts[i] = part.replace(/\//g, '\\/').replace(/#/g, '\\#');
          }
          // start with ``path/filename.md``
          var section_id = parts[0] + parts[1];
          if (section_id.startsWith('/')) {
            section_id = section_id.slice(1);
          }
          var numbers = [];
          if (parts[2]) {
            // append the section path
            var j, hashes;
            for (i = 3; i < l; i = i + 2) {
              hashes = '';
              for (j = 1; j < (i + 1) / 2; j++) {
                hashes += '#';
              }
              numbers.push(parts[i - 1]);
              section_id = section_id + hashes + parts[i];
            }
          }
          if (numbers.length) {
            return section_id + ' ord:' + numbers.join(':');
          }
          else {
            return section_id;
          }
        },
        '_store_section_version': function (section_id, rev, content) {
          this._section_hashes[section_id] = Crypto.SHA256(content);
          this._section_revs[section_id] = rev;
        },
        '_insert_content': function (path, filename, section_path, rev, content, sections) {
          log('Editor._insert_content');
          var content = $.trim(content);
          var section_id = this._generate_section_id(path, filename, section_path, sections);
          var range = this.bespin_editor.selection;
          var current_text = this.bespin_editor.selectedText;
          var start_comment = '<!-- section:' + section_id + ' -->\n\n';
          var end_comment = '\n\n<!-- end section:' + section_id + ' -->';
          var new_text = current_text + start_comment + content + end_comment;
          this.bespin_editor.replace(range, new_text, false);
          this._store_section_version(section_id, rev, content);
        },
        '_handle_drop': function (event, ui) {
          log('dropped!');
          if (this.bespin_editor) {
            var target = $(ui.draggable);
            var stub = target.get(0).id.split('-').slice(1).join('-');
            var parts = stub.split(':');
            var target_id = parts[0];
            var section_path = parts.slice(1).join(':');
            log('target_id: ' + target_id);
            log('section_path: ' + section_path);
            var doc_cache = $('#editor').get(0).doc_cache;
            doc_cache.get_document(
              target_id,
              $.proxy(
                function (doc) {
                  if (doc) {
                    var content = target.data('content');
                    if (content) {
                      this._insert_content(
                        target.data('path'), 
                        target.data('filename'), 
                        section_path, 
                        target.data('rev'), 
                        content,
                        doc.get_sections()
                      );
                    }
                    else {
                      this._insert_content(
                        doc.path, 
                        doc.filename, 
                        section_path,
                        doc._rev, 
                        doc.content,
                        doc.get_sections()
                      );
                    }
                  }
                },
                this
              )
            );
          }
        },
        'init': function (doc) {
          var id_no = this._generate_tabs_id();
          var tab_id = '#tabs-' + id_no;
          var t = $('#editor .tabs');
          if (doc) {
            this.id = doc._id;
            this.rev = doc._rev;
            this.path = doc.path;
            this.initial_content = doc.content;
            this._section_revs = doc.dependencies;
            var sections_by_id = thruflo.markdown.get_section_content_by_id(doc.content);
            var i, l = sections_by_id.length, section;
            for (i = 0; i < l; i++) {
              section = sections_by_id[i];
              this._section_hashes[section['id']] = Crypto.SHA256(section['content']);
            }
            t.tabs('add', tab_id, this._trim_title(doc.filename));
          }
          else {
            this.id = Math.uuid();
            this.rev = null;
            this.path = '/';
            this.initial_content = '\n# ' + this.UNTITLED + ' ' + id_no + '\n\n\n';
            t.tabs('add', tab_id, this.UNTITLED + ' ' + id_no);
          }
          this.tab = $('li', t).last().get(0);
          $('.tab-button', this.tab).click($.proxy(this, 'close'));
          $(document).bind('document:changed', $.proxy(this, 'handle_document_changed'));
          $(document).bind('document:deleted', $.proxy(this, 'handle_document_deleted'));
          var container = $(tab_id).find('.bespin-container');
          bespin.useBespin(container.get(0)).then(
            $.proxy(
              function (env) {
                this.bespin = env;
                this.bespin_editor = env.editor;
                // default the content to something friendly
                this.bespin_editor.value = this.initial_content;
                this.bespin_editor.setLineNumber(4);
                this.focus();
                container.droppable({
                    'accept': 'li.listing',
                    'hoverClass': 'ui-state-active',
                    'drop': $.proxy(this, '_handle_drop')
                  }
                );
                // handle events
                // this.bespin_editor.textChanged.add(this.handle_text_change);
                // this.bespin_editor.selectionChanged.add(this.handle_selection_change);
              },
              this
            ),
            function (error) {
              throw new Error("Launch failed: " + error);
            }
          );
          // provide a dom handle
          this.tab.editor = this;
        },
        'focus': function () {
          if (this.bespin_editor) {
            var e = this.bespin_editor;
            var set_focus = function () { 
              e.focus = true;
            };
            window.setTimeout(set_focus, 10);
          }
        },
        'save': function () {
          if (this.bespin_editor) {
            var content = this.bespin_editor.value;
            var sections = [];
            var sections_by_id = thruflo.markdown.get_section_content_by_id(content);
            log('get_section_content_by_id');
            log(sections_by_id);
            var i,
                l = sections_by_id.length,
                section,
                section_id,
                section_hash;
            for (i = 0; i < l; i++) {
              section = sections_by_id[i];
              section_id = section['id'];
              if (this._section_revs.hasOwnProperty(section_id)) {
                section['rev'] = this._section_revs[section_id];
                section_hash = Crypto.SHA256(section['content']);
                if (this._section_hashes.hasOwnProperty(section_id)) {
                  if (section_hash == this._section_hashes[section_id]) {
                    section['changed'] = false;
                  }
                  else {
                    log('changed!');
                    section['changed'] = true;
                  }
                }
              }
              sections.push(section);
            }
            var filename = this._get_filename(content);
            if (!filename) {
              alert('please add a heading (@@ make nice prompt)');
            }
            else {
              var url = current_path + '/overwrite';
              var params = {
                'filename': filename,
                'content': content,
                'path': this.path,
                'client_id': client_id,
                'dependencies': JSON.stringify(sections)
              };
              if (this.id && this.rev) {
                params['_id'] = this.id;
                params['_rev'] = this.rev;
              }
              else {
                var url = current_path + '/create';
              }
              var self = this;
              $.ajax({
                  'url': url,
                  'type': 'POST',
                  'dataType': 'json',
                  'data': params,
                  'success': function (data) {
                    // store the new doc data
                    var prev_id = self.id;
                    self.id = data['_id'];
                    self.rev = data['_rev'];
                    $.extend(self._section_revs, data['dependencies']);
                    var i, l = sections_by_id.length, section;
                    for (i = 0; i < l; i++) {
                      section = sections_by_id[i];
                      if (!section.hasOwnProperty('changed') || section['changed']) {
                        self._section_hashes[section['id']] = Crypto.SHA256(
                          section['content']
                        );
                      }
                    }
                    // update the tab label
                    var label = self._trim_title(filename);
                    $(self.tab).find('span').text(label);
                    // register with the EditorManager
                    var editor_manager = $('#editor').get(0).editor_manager;
                    if (self.id != prev_id) {
                      editor_manager.reregister(prev_id, self.id, self);
                    }
                    else {
                      editor_manager.register(self.id, self);
                    }
                  },
                  'error': function (transport, text_status) {
                    log('@@ save failed');
                    log(transport.responseText);
                  },
                  'complete': function () {
                    self.focus();
                  }
                }
              );
            }
          }
        },
        'move': function () {},
        'delete_': function () {
          if (!this.rev) {
            this.close();
          }
          else {
            var self = this;
            var url = current_path + '/delete';
            var params = {
              '_id': this.id, 
              '_rev': this.rev,
              'client_id': client_id
            };
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
          var editor_manager = $('#editor').get(0).editor_manager;
          editor_manager.unregister(this.id);
          var tab_button = $('.tab-button', this.tab);
          tab_button.unbind('click');
          var i = $('li', $('#editor .tabs')).index(this.tab);
          $('#editor .tabs').tabs('remove', i);
          editor_manager.refresh_selected();
        },
        'update': function (doc) {
          if (doc._id == this.id) {
            if (this.bespin_editor.value != doc.content) {
              if (
                confirm(
                  this._get_filename(this.bespin_editor.value) + 
                  " has changed." + 
                  " Are you sure you want to revert to the saved version?"
                )
              ) {
                this.id = doc._id;
                this.rev = doc._rev;
                this.bespin_editor.value = doc.content;
              }
            }
          }
        },
        'handle_document_changed': function (event, data) {
          
          log('handle_document_changed');
          log(data);
          
          // we have the filename and path
          
          var stub = data['path'] + data['filename'];
          if (stub.startsWith('/')) {
            stub = stub.slice(1);
          }
          
          // if that matches our sections list
          
          var matched = [];
          var content = this.bespin_editor.value;
          var sections_by_id = thruflo.markdown.get_section_content_by_id(content);
          var i, 
              section, 
              section_id, 
              l = sections_by_id.length;
          for (i = 0; i < l; i++) {
            section = sections_by_id[i];
            section_id = section['id'];
            if (section_id.startsWith(stub)) {
              matched.push(section);
            }
          }
          
          if (matched.length) {
            // get the new, uptodate sections
            var doc_cache = $('#editor').get(0).doc_cache;
            var doc = doc_cache.get_document(
              data['_id'],
              $.proxy(
                function (doc) {
                  if (doc) {
                    /*
                      
                      we want to compare the section content parsed out of our doc
                      with the content that comes from the doc's sections
                      
                    */
                    var our_section, 
                        docs_section = null,
                        has_changed;
                    for (i = 0; i < matched.length; i++) {
                      our_section = matched[i];
                      // get the doc section 
                      var docid_or_sections_key = this._get_docid_or_sections_key(
                        doc.repository, 
                        doc._id, 
                        section['id']
                      );
                      if (!(docid_or_sections_key instanceof Array)) {
                        docs_section = $.trim(doc.content);
                      }
                      else {
                        var sections = doc.get_sections();
                        for (var j = 0; j < sections.length; j++) {
                          if (sections[j][0] == docid_or_sections_key) {
                            docs_section = sections[j][1];
                          }
                        }
                      }
                      if (!docs_section) {
                        log('*** @@ need to unpin when section not found ***');
                      }
                      else {
                        has_changed = !(our_section == docs_section);
                        var should_store_section_version = !has_changed;
                        if (has_changed) {
                          // if so, prompt
                          if (
                            confirm(
                              '@@ ' + doc.filename + ' contains ' + section['id'] + 
                              ' which has been updated. ' + 
                              ' Do you want to overwrite that section in ' + 
                              doc.filename + '?'
                            )
                          ) {
                            // insert the new content into the doc at the right place
                            var new_content = thruflo.markdown.get_updated_dependency_content(
                              content,
                              section['id'],
                              docs_section
                            );
                            this.bespin_editor.value = new_content;
                            this.bespin.dimensionsChanged();
                            should_store_section_version = true;
                          }
                        }
                        if (should_store_section_version) {
                          this._store_section_version(
                            section['id'], 
                            data['_rev'], 
                            docs_section
                          );
                        }
                      }
                    }
                  }
                },
                this
              )
            );
          }
        },
        'handle_document_deleted': function (event, data) {
          log('@@ todo: handle_document_deleted');
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
    var ListingsManager = SingleContextBase.extend({
        '_handle': 'listings_manager',
        '_sort_by': 'filename', // | mod
        '_current_preview': null,
        'listing_template': $.template(
          '<li id="listing-${id}" class="listing document-listing">\
            <span class="listing-title">\
              <a href="#${id}" title="${filename}"\
                  thruflo:mod="${mod}">\
                ${filename}\
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
        'insert': function (context, _id, filename, mod, should_not_sort) {
          if (!context) {
            existing = $('#listing-' + _id, this.context);
            existing.find('*').unbind();
            existing.remove();
            
            $("li[id*='preview-" + _id + "']").remove();
            
            $(this.context).append(
              this.listing_template, {
                'id': _id,
                'filename': filename,
                'mod': mod
              }
            );
            context = $('#listing-' + _id, this.context).get(0);
          }
          var listing = new Listing(context, _id, filename);
          if (!should_not_sort) {
            this.sort();
          }
        },
        'remove': function (context, _id) {
          if (!context) {
            context = $('#listing-' + _id, this.context);
          }
          context.find('*').unbind();
          context.remove();
          
          $("li[id*='preview-" + _id + "']").remove();
          
          this.sort();
        },
        'sort': function () {
          $('.listing', this.context).tsort(
            "span.listing-title a", {
              'attr': this._sort_by == 'filename' ? 'title' : 'thruflo:mod'
            }
          );
        },
        'init': function (context_id) {
          this._super(context_id);
          var self = this;
          $('.listing', this.context).each(
            function () {
              var _id = this.id.split('listing-')[1];
              var link = $(this).find('a').eq(0);
              var filename = link.attr('title');
              var mod = link.attr('thruflo:mod');
              self.insert(this, _id, filename, mod, true);
            }
          );
          this.sort();
        }
      }
    );
    var Listing = SingleContextBase.extend({
        '_handle': 'listing',
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
        '_generate_helper': function (event) {
          var title = $(this).find('span > a').first().attr('title');
          return $('<div class="insert-section-helper">' + title + '</div>');
        },
        '_ensure_has_doc': function (callback) {
          $('#editor').get(0).doc_cache.get_document(
            this._id, 
            $.proxy(
              function (doc) {
                if (doc) {
                  this.doc = doc;
                  this.sections = doc.get_sections();
                  callback();
                }
              },
              this
            )
          );
        },
        '_get_type': function () {
          if (!this.hasOwnProperty('_type')) {
            var resource_listing = $(this.context).parents('.resource-listing').get(0);
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
              level,
              hashes,
              path_items,
              path,
              parent_path,
              parent_id,
              parent,
              section_id,
              rendered_section;
          
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
            for (j = 1; j < k; j++) {
              key_item = key[j];
              if (j == k || key[j + 1] != null) {
                path_items.push(encodeURIComponent(key_item));
              }
              else {
                break;
              }
            }
            
            level = path_items.length / 2;
            hashes = '';
            for (j = 0; j < level; j++) {
              hashes += '#';
            }
            
            path = this._id + ':' + path_items.join(':');
            title = decodeURIComponent(path_items.pop());
            
            path_items.pop();
            parent_path = this._id + ':' + path_items.join(':');
            if (parent_path.endsWith(':')) {
              parent_path = parent_path.slice(0, -1);
            }
            parent_id = 'sections:' + parent_path;
            parent_id = parent_id.makeSelectorSafe();
            
            // insert the section markup
            
            parent = $('#' + parent_id);
            parent.append(
              this._section_template, {
                'path': path,
                'type': this._get_type(),
                'title': title,
              }
            );
            
            // make the section heading a draggable
            
            section_id = '#section-' + path;
            rendered_section = $(section_id.makeSelectorSafe(), parent);
            rendered_section.draggable({
                'helper': this._generate_helper,
                'appendTo': 'body'
              }
            );
            
            // store the content against it
            
            rendered_section.data('content', hashes + ' ' + title + '\n' + value);
            rendered_section.data('path', this.doc.path);
            rendered_section.data('filename', this.doc.filename);
            rendered_section.data('rev', this.doc._rev);
            
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
            var link = $('span.section-title a', this.context);
            // link.click($.proxy(this, 'select'));
            // link.dblclick($.proxy(this, 'open'));
            link.fixClick($.proxy(this, 'select'), $.proxy(this, 'open'));
            this._rendered = true;
          }
        },
        '_trigger_open': function () {
          $('#editor').get(0).editor_manager.open(this.doc);
        },
        'init': function (context, _id, filename) {
          this.doc = null;
          this.sections = null;
          this._rendered = false;
          this.context = context;
          this._id = _id;
          this.filename = filename;
          $(this.context).draggable({
              'helper': this._generate_helper,
              'appendTo': 'body'
            }
          );
          var link = $(this.context).find('a').first();
          // link.click($.proxy(this, 'select'));
          // link.dblclick($.proxy(this, 'open'));
          link.fixClick($.proxy(this, 'select'), $.proxy(this, 'open'));
          this.context.listing = this;
        },
        'select': function (event) {
          if (event) { event.stopPropagation(); }
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
        'open': function (event) {
          if (event) { event.stopPropagation(); }
          this._ensure_has_doc($.proxy(this, '_trigger_open'));
        }
      }
    );
    
    $(document).ready(
      function () {
        
        /*
          
          patch bespin
          
        */
        
        bespin.base = '/static/bespin';
        
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
              <div class="bespin-container"></div>\
            </div>',
            'add': function (event, ui) {
              $('#editor .tabs').tabs('select', '#' + ui.panel.id);
            },
            'select': function (event, ui) {
              var editor_manager = $('#editor').get(0).editor_manager;
              var tab = $(ui.tab).closest('li').get(0);
              var target_editor = tab.editor;
              if (target_editor) {
                var editor_id = target_editor.id;
                editor_manager.select(editor_id);
              }
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
        
      }
    );
})(jQuery);
