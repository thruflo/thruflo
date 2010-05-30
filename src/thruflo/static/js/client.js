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
    var templates = {
      'blob': $.template('<div id="${id}" class="blob">${data}</div>')
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
    $("#repository-browser").treeview({
        'animated': 'fast',
        'collapsed': true,
        'unique': true,
        'persist': 'cookie',
        'toggle': function () {
          log(this);
        }
      }
    );
    $('#sections-container').droppable({
        'activeClass': 'ui-state-default',
        'hoverClass': 'ui-state-hover',
        'accept': 'li.file',
        'drop': function (event, ui) {
          var container = $(this);
          var parts = ui.draggable.attr('id').split('/');
          var params = {
            'repo': parts.slice(0, 2).join('/'),
            'branch': parts[2],
            'path': parts.slice(3).join('/')
          }
          $.ajax({
              'url': current_path + '/insert',
              'type': 'POST',
              'dataType': 'json',
              'data': params,
              'success': function (data) {
                container.append(templates['blob'], data);
                
                // @@ apply beahviour
                
                
              }
            }
          );
          
        }
      }
    ).sortable({
        'items': 'div.blob',
        'sort': function() {
          $(this).removeClass('ui-state-default');
        }
      }
    );
    // if we're on the document UI page, open a websocket to
    // handle live updates
    if ($("#repository-browser").length) {
      var poller = {
        'min': 100,
        'max': 4000,
        'multiplier': 1.5,
        'backoff': 1000
      };
      poller.poll = function () {
        $.ajax({
            'url': current_path + '/listen',
            'type': 'POST',
            'dataType': 'json',
            'data': {},
            'success': function (data) {
              if (data) {
                log('@@ handle data');
                log(data);
              }
            },
            'complete': function (transport, text_status) {
              var status = parseInt(text_status);
              if (status < 300) {
                poller.backoff = poller.min;
              }
              else {
                poller.backoff = poller.backoff * poller.multiplier;
                if (poller.backoff > poller.max) {
                  poller.backoff = poller.max;
                }
              }
              window.setTimeout(poller.poll, poller.backoff);
            }
          }
        );
      };
      poller.poll();
    }
  }
);