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
    $('.tabs').tabs();
    $('.accordion').accordion();
    $('.ui-draggable').draggable(draggable_options);
    $('#selected-container, #unselected-container').droppable({
        'activeClass': 'ui-state-default',
        'hoverClass': 'ui-state-hover',
        'accept': 'li.ui-draggable',
        'drop': function (event, ui) {
          var container = $(this);
          var target = ui.draggable;
          var form = target.find('form');
          var other, action;
          if (container.attr('id') == 'selected-container') {
            action = 'select';
          }
          else {
            action = 'unselect';
          }
          $.ajax({
              'url': current_path + '/' + action,
              'type': 'POST',
              'dataType': 'json',
              'data': form.serialize(),
              'success': function (data) {
                container.find('ul.repositories-list').append(target.detach());
              }
            }
          );
        }
      }
    ).sortable({
        'items': 'div.section',
        'sort': function() {
          $(this).removeClass('ui-state-default');
        }
      }
    );
  }
);