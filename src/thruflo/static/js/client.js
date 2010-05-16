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
    var templates = {
      'section': $.template(
        '<div id="${id}" class="section ${type}">${type}</div>'
      )
    };
    var draggable_options = {
        'appendTo': 'body', 
        'helper': 'clone',
        'cursor': 'crosshair',
        'containment': 'document',
        'delay': 250,
        'distance': 20,
        'scroll': true
        // 'revert': true
    };
    // initialise UI components
    $('.tabs').tabs();
    $('.accordion').accordion();
    $('.ui-draggable').draggable(draggable_options);
    // setup one size fits all content object editing
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
    // setup document UI behaviour
    var inspector_tabs = $('#inspector > .tabs');
    var sections_tab = $('#tabs-sections');
    var sections_tab_sections = sections_tab.find('div.section-type');
    var sections_container = $('#sections-container');
    var insert_units = function (section, content_type, content_id) {
      var section_type = section.data('section_type');
      var current_path = window.location.pathname;
      if (current_path.endsWith('/')) {
        current_path = current_path.slice(0, -1);
      }
      $.ajax({
          'url': current_path + '/map',
          'type': 'POST',
          'dataType': 'json',
          'data': {
            'section_type': section_type,
            'content_type': content_type,
            'content_id': content_id
          },
          'beforeSend': function () {},
          'error': function (transport) {
            log(transport.responseText);
            // data = $.parseJSON();
          },
          'success': function (data) {
            log(data);
            // @@ ...
            
            
          }
        }
      );
    };
    var select_section = function (section) {
      var section_type = section.data('section_type');
      sections_container.find('div.section').removeClass('selected');
      section.addClass('selected');
      sections_tab.find('div.section-type').hide();
      sections_tab.find('div.section-type.' + section_type).show();
      inspector_tabs.tabs("select", "sections");
    };
    var insert_new_section = function (section_type) { 
      var section_id = Math.uuid();
      sections_container.append(
        templates['section'], {
          'type': section_type, 'id': section_id
        }
      );
      var section = $('#' + section_id);
      section.data('section_type', section_type);
      // make the section droppable
      section.droppable({
          'activeClass': 'ui-state-default',
          'hoverClass': 'ui-state-hover',
          'accept': 'li.content-type',
          'drop': function (event, ui) {
            var parts = ui.draggable.attr('id').split('--');
            insert_units(section, parts[0], parts[1]);
          }
        }
      ).sortable({
          'items': 'div.unit',
          'sort': function() {
            $(this).removeClass('ui-state-default');
          }
        }
      );
      // make it selectable
      section.bind(
        'click dblclick', 
        function (event) {
          select_section($(this));
        }
      );
      $(document).bind(
        'keyup', 
        function (event) {
          if (event.keyCode == 74) {
            // select down
            var current_section = container.find('div.section.selected');
            current_section.next('div.section').click();
          }
          else if (event.keyCode == 75) {
            // select up
            var current_section = container.find('div.section.selected');
            current_section.prev('div.section').click();
          }
        }
      );
      // select it
      section.click();
    };
    sections_tab.find('div.section-type').hide();
    sections_container.droppable({
        'activeClass': 'ui-state-default',
        'hoverClass': 'ui-state-hover',
        'accept': 'li.section-type',
        'drop': function (event, ui) {
          var section_type = ui.draggable.attr('id');
          insert_new_section(section_type);
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