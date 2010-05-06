var log = function (what) {
  try { console.log(what); }
  catch (err) {}
};
jQuery(document).ready(
  function ($) {
    
    $('.tabs').tabs();
    
    $('form.ajax').submit(
      function () {
        var target = $(this);
        var url = target.attr('action');
        var params = target.serialize();
        $.ajax({
            'url': url,
            'type': 'POST',
            'dataType': 'json',
            'data': params,
            'success': function (data) {
              log(data);
            }
          }
        );
        return false;
      }
    );
  }
);