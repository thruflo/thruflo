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
        $('.tabs').tabs();
        $('.accordion').accordion();
      }
    );
})(jQuery);
