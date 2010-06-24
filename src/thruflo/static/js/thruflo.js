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
        var a = $('#editor .accordion').accordion();
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
              <iframe src="/bespin" width="420px" height="420px">\
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
        var UNTITLED = 'Untitled',
            current_document,
            intid = 1;
        var Document = Class.extend({
            '_generate_id': function () {
              var id = intid;
              intid += 1;
              return id;
            },
            '_get_index': function () {
              return $('li', t).index(this.tab);
            },
            'init': function () {
              var self = this;
              // render tab
              var id_no = this._generate_id();
              var tab_id = '#tabs-' + id_no;
              t.tabs('add', tab_id, UNTITLED + ' ' + id_no);
              this.tab = $('li', t).last();
              // wait for the editor to be ready
              var panel = $(tab_id);
              var frame = $('iframe', panel).get(0);
              frame.contentWindow.onBespinLoad = function () {
                log('bespin loaded');
                // get a handle on the editor
                var doc = frame.contentWindow.document;
                self.bespin = $('#editor', doc).get(0).bespin;
                self.editor = self.bespin.editor;
                // default the content to something friendly
                self.editor.value = '\n# ' + UNTITLED + ' ' + id_no + '\n\n\n';
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
                  if (index == self._get_index()) {
                    if (typeof(self.editor) != 'undefined') {
                      self.editor.focus = true;
                    }
                    current_document = self;
                  }
                }
              );
              // ensure we're now the current document
              $(document).trigger('thruflo:tab:selected', [this._get_index()]);
            },
            'open': function () {},
            'save': function () {
              log('save: ' + this._get_index());
              var content = this.editor.value;
              var html = convertor.makeHtml(content);
              if (html.startsWith('<h1>')) {
                // we have a heading
                $.ajax({
                    'url': current_path + '/save',
                    'type': 'POST',
                    'dataType': 'json',
                    'data': {
                      'content': content,
                      'path': '/' // @@ folder path
                    },
                    'success': function (data) {
                      
                      log('@@ handle saved OK');
                      log(data);
                      
                      
                    },
                    'error': function (transport, text_status) {
                      log(transport.responseText);
                    },
                    'complete': function () {}
                  }
                );
              }
              else {
                // we need to add a heading
                alert('please add a heading (@@ make nice prompt)');
              }
            },
            'saveas': function () {
              log('saveas: ' + this._get_index());
            },
            'move': function () {},
            'delete_': function () {},
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
        });
        
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
        $('#saveas-document').bind(
          'click dblclick',
          function () {
            current_document.saveas();
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
