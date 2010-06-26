String.prototype.startsWith = function (pattern) {
  return this.indexOf(pattern) === 0;
};
String.prototype.endsWith = function (pattern) {
  var d = this.length - pattern.length;
  return d >= 0 && this.lastIndexOf(pattern) === d;
};
(function ($) {
    var log = function (what) {
      try { 
        console.log(what); 
      }
      catch (err) {
        // pass
      }
    };
    $(document).ready(
      function () {
        var current_path = window.location.pathname;
        if (current_path.endsWith('/')) {
          current_path = current_path.slice(0, -1);
        };
        var draggable_options = {
          'appendTo': 'body', 
          'helper': 'clone',
          'cursor': 'crosshair',
          'containment': 'document',
          'delay': 250,
          'distance': 20,
          'scroll': true
        };
        var stop_accordion;
        $('#editor .accordion').click(
          function (event) {
            if (stop_accordion) {
              event.stopImmediatePropagation();
              event.preventDefault();
              stop_accordion = false;
            }
          }
        );
        var a = $('#editor .accordion').accordion({
            'autoHeight': false,
            'collapsible': true
          }
        ).sortable({
            'axis': "y",
            'handle': "h3",
            'stop': function (event, ui) {
              stop_accordion = true;
            }
          }
        );
        var t = $('#editor .tabs').tabs({
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
              t.tabs('select', '#' + ui.panel.id);
            },
            'select': function (event, ui) {
              var tab = $(ui.tab).parent();
              var i = $('li', t).index(tab);
              $(document).trigger('thruflo:tab:selected', [i]);
            }
          }
        );
        var convertor = new Showdown.converter();
        var nl = '[\n\r\u2028\u2029\u0085]';
        var dot = '[^\n\r\u2028\u2029\u0085]';
        var leading_whitespace = XRegExp('^[\\p{Zs}\n\r\u2028\u2029\u0085]+');
        var leading_atx_h1 = XRegExp(
          '^\#\\p{Zs}*(' + dot + '+)\\p{Zs}*\#*' + nl
        );
        var leading_setext_h1 = XRegExp(
          '^(' + dot + '+)\\p{Zs}*' + nl + '=+\\p{Zs}*' + nl
        );
        var UNTITLED = 'Untitled';
        var current_document;
        var intid = 1;
        var Document = Class.extend({
            '_generate_tabs_id': function () {
              var id = intid;
              intid += 1;
              return id;
            },
            '_get_tabs_index': function () {
              return $('li', t).index(this.tab);
            },
            '_get_title': function (content) {
              /*
                
                Extracts document title from the opening H1
                in the markdown content.
                
                If the first non-whitespace in the document 
                content isn't a valid setext or atx H1 then
                returns null.
                
                
              */
              if (content.length > 500) {
                content = content.slice(0, 500);
              }
              content = content.replace(leading_whitespace, '');
              var title = leading_atx_h1.exec(content);
              if (!title) {
                title = leading_setext_h1.exec(content);
                if (!title) {
                  return null;
                }
              }
              return title[1];
            },
            '_trim_title': function (title) {
              if (title.length > 20) {
                title = title.slice(0, 16) + ' ...';
              }
              return title;
            },
            'init': function (doc) {
              var id_no = this._generate_tabs_id();
              var tab_id = '#tabs-' + id_no;
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
                this.initial_content = '\n# ' + UNTITLED + ' ' + id_no + '\n\n\n';
                t.tabs('add', tab_id, UNTITLED + ' ' + id_no);
              }
              this.tab = $('li', t).last();
              // wait for the editor to be ready
              var panel = $(tab_id);
              var frame = $('iframe', panel).get(0);
              var self = this;
              frame.contentWindow.onBespinLoad = function () {
                log('bespin loaded');
                // get a handle on the editor
                var doc = frame.contentWindow.document;
                self.bespin = $('#editor', doc).get(0).bespin;
                self.editor = self.bespin.editor;
                // default the content to something friendly
                self.editor.value = self.initial_content;
                self.editor.setLineNumber(4);
                self.editor.focus = true;
                // handle events
                self.editor.textChanged.add(self.handle_text_change);
                self.editor.selectionChanged.add(self.handle_selection_change);
              };
              // apply event handling
              $('.tab-button', this.tab).bind(
                'click dbclick', 
                function () {
                  self.close();
                }
              );
              $(document).bind(
                'thruflo:tab:selected',
                function (event, index) {
                  log('thruflo:tab:selected: ' + index);
                  if (index == self._get_tabs_index()) {
                    if (typeof(self.editor) != 'undefined') {
                      self.editor.focus = true;
                    }
                    current_document = self;
                  }
                }
              );
              // ensure we're now the current document
              $(document).trigger('thruflo:tab:selected', [this._get_tabs_index()]);
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
        
        var Listing = Class.extend({
            '_has_data': function () {
              return !!(this.doc);
            },
            '_fetch_data': function (callback) {
              var self = this;
              $.ajax({
                  'url': current_path + '/fetch',
                  'type': 'POST',
                  'dataType': 'json',
                  'data': {'_id': this._id},
                  'success': function (data) {
                    self.doc = data['doc'];
                    self.sections = data['sections'];
                    self._render_sections();
                    callback();
                  },
                  'error': function (transport, text_status) {
                    log('@@ fetch failed');
                    log(transport.responseText);
                  }
                }
              );
            },
            '_render_sections': function () {
              log('@@ render sections');
              log(this.sections);
            },
            '_show_sections': function () {
              log('@@ show sections');
            },
            '_trigger_open': function () {
              $(document).trigger('thruflo:document:opened', [this.doc]);
            },
            'init': function (target, _id, title) {
              this.doc = null;
              this.sections = null;
              this.target = target;
              this._id = _id;
              this.title = title;
              var self = this;
              $(this.target).click(
                function (event) {
                  self.select();
                  return false;
                }
              );
              $(this.target).dblclick(
                function (event) {
                  self.open();
                  return false;
                }
              );
            },
            'select': function () {
              if (this._has_data()) {
                this._show_sections();
              }
              else {
                this._fetch_data(this._show_sections);
              }
            },
            'open': function () {
              if (this._has_data()) {
                this._trigger_open();
              }
              else {
                this.fetch_data(this._trigger_open);
              }
            }
          }
        );
        
        $(document).bind(
          'thruflo:document:opened',
          function (event, doc) {
            var d = new Document(doc);
            return false;
          }
        );
        
        $('#documents-listing .listing').each(
          function () {
            var _id = this.id.split('listing-')[1];
            var title = $(this).find('a').eq(0).attr('title');
            this.listing = new Listing(this, _id, title);
          }
        );
        
        // don't think just type
        var d = new Document();
        
        $('#add-new-document-link').bind(
          'click dblclick',
          function () {
            var d = new Document();
            return false;
          }
        );
        $('#save-document').bind(
          'click dblclick',
          function () {
            current_document.save();
            return false;
          }
        );
        $('#delete-document').bind(
          'click dblclick',
          function () {
            current_document.delete_();
            return false;
          }
        );
        $(document).keyup(
          function (event) {
            log(event.keyCode);
          }
        );
      }
    );
})(jQuery);
