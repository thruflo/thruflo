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
                
                var i,
                    commit,
                    l = data['commits'].length;
                for (i = 0; i < l; i++) {
                  commit = data['commits'][i];
                  /*
                    
                    @@ we know data['branch'] and we have lists
                    of ``added``, ``removed`` and ``modified``
                    
                    we need to add the added and remove the removed
                    
                  */
                  
                  log('@@ we need to add the added and remove the removed');
                  
                  
                }
                
                /*
                  
                  @@ we have a list of data['invalid_blobs']
                  
                  we need to filter them against the blobs in
                  the document and refresh those that are
                  
                  
                */
                var invalid_blob_ids = $('#sections-container').find(
                  '.blob'
                ).filter(
                  function (i) {
                    return data['invalid_blobs'].indexOf(this.id) > -1;
                  }
                ).map(
                  function () { 
                    return this.id; 
                  }
                ).get()
                if (invalid_blob_ids.length) {
                  var update_blobs = function (blobs) {
                    $('#sections-container').find('.blob').each(
                      function () {
                        log(this);
                        log(this.id);
                        log(this.id in blobs);
                        if (this.id in blobs) {
                          $(this).html(blobs[this.id]);
                        }
                      }
                    );
                  };
                  var get_blobs_url = current_path.split('/doc/')[0] + '/get_blobs';
                  $.ajax({
                      'url': get_blobs_url,
                      'type': 'GET',
                      'dataType': 'json',
                      'data': {
                        'keys': invalid_blob_ids
                      },
                      'success': function (data) {
                        log('@@ get_blobs success');
                        log(data);
                        update_blobs(data);
                      },
                      'error': function () {
                        log('@@ get_blobs error');
                        $('#sections-container').delay(1000).each(
                          function () {
                            $.ajax({
                                'url': get_blobs_url,
                                'type': 'GET',
                                'dataType': 'json',
                                'data': {
                                  'blobs': invalid_blob_ids
                                },
                                'success': function (data) {
                                  log('@@ get_blobs retry success');
                                  log(data);
                                  update_blobs(data);
                                }
                              }
                            );
                          }
                        );
                      }
                    }
                  );
                }
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