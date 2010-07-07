/*
  
  Scope taming boilerplate.
  
  Allows:
  
      $.registerPlugin(
        'foo', {
          'doit': function () {
            console.log('doit');
            console.log(this);
          },
          'handle': function (event) {
            event.stopPropagation();
            console.log('handle');
            console.log(this);
          },
          'init': function () {
            console.log('init');
            console.log(this);
            $(this).click(this.foo.handle);
          }
        }
      );
      
  With usage like:
  
      $(document).ready(
        function () {
          $('.foo').foo();
          $('#bar').click(
            function () {
              // either
              var targets = $('.foo');
              targets.each(
                function () {
                  this.foo.doit();
                }
              );
              // or simply
              var target = $('.foo').get(0);
              target.foo.doit();
            }
          );
        }
      );
  
  The point being:
  
  * you can fetch your "class" "instances" (sic) from the dom, in nice
    jquery fashion (so you don't have to worry about having a reference
    to them: any code can fetch and call any other code)
  * ``this`` is *always* the original dom element context matched by the
    plugin selector
  
  With one trade off:
  
  * you have to use ``this[namespace][method_name]`` (ala ``this.foo.handle``) 
    instead of this[method_name].
  
  This trade off is not 100% necessary: if you set ``use_namespace`` to ``false``
  then the methods will be hung of the dom element without a namespace.  This is
  great, until you get a clash between multiple plugins.
  
  
*/
  
(function ($) {
    $.registerPlugin = function (namespace, methods, defaults, use_namespace) {
      $.fn[namespace] = function (name, overrides) {
        var options = jQuery.extend(defaults, overrides);
        var should_use_namespace = !(use_namespace === false);
        return this.each(
          function (i) {
            if (!$(this).data(namespace + ':initialised')) {
              if (should_use_namespace) {
                this[namespace] = {};
                $.each(
                  methods, 
                  $.proxy(
                    function (key, value) {
                      this.foo[key] = $.proxy(value, this);
                    }, 
                    this
                  )
                );
                if (methods.hasOwnProperty('init')) {
                  this[namespace].init();
                }
              }
              else {
                $.extend(this, methods);
                if (methods.hasOwnProperty('init')) {
                  this.init();
                }
              }
              $(this).data(namespace + ':initialised', true);
            }
          }
        );
      };
    };
});
