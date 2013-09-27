(function() {

function init() {
  $('#intro').on('click', 'button', function() {
    var happy = $(this).hasClass('happy');

    $('#moreinfo').removeClass(happy ? 'sad' : 'happy');
    $('#moreinfo').addClass(happy ? 'happy' : 'sad');
    $('#happy').val(happy ? '1' : '0');
    $('x-deck')[0].shuffleNext();
  });

  $('button.back').on('click', function() {
    $('x-deck')[0].shufflePrev();
  });

  $('#moreinfo button.next').on('click', function() {
    $('x-deck')[0].shuffleNext();
  });

  $('#country input.country-radio').on('click', function() {
    $('x-deck')[0].shuffleNext();
  });

  $('#device input.device-radio').on('click', function() {
    $('x-deck')[0].shuffleNext();
  });

  $('#email .email-ok input').on('change', function() {
    var on = $(this).is(':checked');
    $('#email .email').toggle(on);
    $('#privacy-email').toggle(on);
  });
  $('#email-ok').change();

  $('button.complete').on('click', function() {
    var data = {
      'happy': $('#happy').val(),
      'description': $('#description').val(),
      'product': 'Firefox OS',
      'platform': 'Firefox OS',
      'locale': $('#locale').val(),
      'country': $('input.country-radio').val(),
      'manufacturer': $('input.device-radio').val().split('::')[0],
      'device': $('input.device-radio').val().split('::')[1]
    };

    // FIXME - figure out Firefox OS version from Gecko version in UA
    if ($('#email-ok').val()) {
      data['email'] = $('#email-input').val()
    }

    console.log(data);
    // var jqxhr = $.post(
    //     '/api/v1/feedback/',
    //     data,
    //     function() {
    //       // FIXME - redirect to thanks
    //     },
    //     'json');
  });
}

$(init);

})();
