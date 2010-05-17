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
jQuery(document).ready(
  function ($) {
    var _xsrf = '', get_xsrf = function () {
      if (!_xsrf) {
        _xsrf = $.cookie('_xsrf');
      }
      return _xsrf;
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
    $('.ui-draggable').draggable(draggable_options);
  }
);