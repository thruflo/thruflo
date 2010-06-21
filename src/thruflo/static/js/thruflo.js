String.prototype.endsWith = function (pattern) {
  var d = this.length - pattern.length;
  return d >= 0 && this.lastIndexOf(pattern) === d;
};
(function ($) {
    $.fn.document = function (tabview, options) {
      var templates = {
        'tab': $.template(
          '<li>\
            <a href="#${id}">\
              <div class="tab-button-container">\
                <a href="#close" class="tab-button close">[ x ]</a>\
                <a href="#changed" class="tab-button changed">[ O ]</a>\
              </div>\
              <div class="filename">${filename}</span>\
            </a>\
          </li>'
        )
      };
      var defaults = {
        'id': null,
        'filename': null,
        'filepath': null,
        'is_new': true
      };
      var settings = $.extend(defaults, options);
      var methods = {
        'init': function () {
          if (settings.is_new) {
            // render empty
            
            
          }
          else {
            // render content
            
            
          }
        }
      };
      return this.each(
        function () {
          $.extend(this, methods);
          this.init();
        }
      );
    };
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
        var templates = {
          // 'blob': $.template('<div id="${id}" class="blob">${data}</div>')
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
        var editor = {
          'tabs': $('#editor .tabs').tabs(),
          'accordion': $('#editor .accordion').accordion()
        };
        
        var Document = Class.extend({
            'init': function () {
              
              // add the tab
              // add the panel
              // render the bespin editor
              // etc.
              
              
            },
            'open': function () {},
            'save': function () {},
            'saveas': function () {},
            'move': function () {},
            'delete': function () {},
            'insert': function () {},
            'unpin': function () {},
            'preview': function () {},
            'validate': function () {},
            'expand': function () {},
            'collapse': function () {},
            'close': function () {}
        });
        
        
      }
    );
})(jQuery);
