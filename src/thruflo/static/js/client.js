var log = function (what) {
  try { console.log(what); }
  catch (err) {}
};
jQuery(document).ready(
  function ($) {
    
    $('.tabs').tabs();
    $('.accordion').accordion();
    
    $('input[type=submit]').live(
      'click dblclick', 
      function () {
        var target = $(this);
        var form = target.parents('form').first();
        form.attr('submit_value', target.attr('value'));
      }
    );
    
    $('form.ajax').submit(
      function () {
        var target = $(this);
        var url = target.attr('action');
        var submit_value = target.attr('submit_value');
        if (submit_value == 'Fork') {
          url = url.replace('/save/', '/fork/');
        }
        var params = target.serialize();
        var error_div = target.find('div.error');
        var textarea = target.find('textarea');
        var fork_button = target.find('input[type=submit][value=Fork]');
        var save_button = target.find('input[type=submit][value=Save]');
        var psid_input = target.find('input[name=section_id]');
        $.ajax({
            'url': url,
            'type': 'POST',
            'dataType': 'json',
            'data': params,
            'beforeSend': function () {
              error_div.empty();
            },
            'error': function (transport) {
              var data = {'errors': {'500': 'System Error.'}};
              try {
                data = $.parseJSON(transport.responseText);
              }
              catch (err) {}
              var k;
              for (k in data['errors']) {
                error_div.append(
                  '<p>' + k + ': ' + data['errors'][k] + '</p>'
                );
              }
            },
            'success': function (data) {
              if (submit_value == 'Fork') {
                log('@@ todo: insert form markup');
              }
              else {
                if (!psid_input.length) {
                  log('inserting psid_input...');
                  target.append(
                    '<input type="hidden" \
                        name="section_id" \
                        value="' + data['doc']['_id'] + '" \
                    />'
                  );
                  psid_input = target.find('input[name=section_id]');
                }
                if (!fork_button.length) {
                  log('inserting fork_button...');
                  save_button.parent().after(
                    '<div class="form-row"> \
                      <input type="submit" value="Fork" /> \
                      <input type="text" name="fork_name" value="" /> \
                    </div>'
                  );
                  fork_button = target.find('input[type=submit][value=Fork]');
                }
                textarea.effect("highlight", {}, 1500);
              }
            }
          }
        );
        return false;
      }
    );
    
    $('#inspector .ui-draggable').draggable({
        'appendTo': 'body', 
        'helper': 'clone',
        'cursor': 'crosshair',
        'containment': 'document',
        'delay': 250,
        'distance': 20,
        'scroll': true
        // 'revert': true
    });
    $('#sections-container').droppable({
        'activeClass': 'ui-state-default',
        'hoverClass': 'ui-state-hover',
        'accept': ':not(.ui-sortable-helper)',
        'drop': function (event, ui) {
          // $(this).find('.placeholder').remove();
          // $('<li></li>').text(ui.draggable.text()).appendTo(this);
          log(ui.draggable);
        }
    });
    /*.sortable({
        items: 'li:not(.placeholder)',
        sort: function() {
          // gets added unintentionally by droppable interacting with sortable
          // using connectWithSortable fixes this, but doesn't allow you to customize active/hoverClass options
          $(this).removeClass('ui-state-default');
        }
      });
    });
    */
  }
);