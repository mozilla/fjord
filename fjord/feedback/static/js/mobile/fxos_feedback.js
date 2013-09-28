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

  $('#country input:radio').on('click', function(ev) {
    if (window.localStorage) {
      localStorage['country'] = $('#country input:radio:checked').val();
    }
    $('x-deck')[0].shuffleNext();
  });

  $('#device input:radio').on('click', function() {
    if (window.localStorage) {
      localStorage['device'] = $('#device input:radio:checked').val();
    }
    $('x-deck')[0].shuffleNext();
  });

  $('#email .email-ok input').on('change', function() {
    var on = $(this).is(':checked');
    $('#email .email').toggle(on);
    $('#privacy-email').toggle(on);
  });

  $('button.complete').on('click', function() {
    var email, data, numCards, jqxhr;

    // verify email address
    if ($('#email-ok:checked').val()) {
      email = $.trim($('#email-input').val());

      // this should be close enough to what django is doing that we
      // can catch issues client-side
      if (!email.match(/^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/)) {
        $('#email-error').show();
        return;
      }

      // in case it was showing, we hide it again
      $('#email-error').hide();

      if (window.localStorage) {
        localStorage['email'] = $('#email-input').val();
      }
    }

    data = {
      'happy': $('#happy').val(),
      'description': $('#description').val(),
      'product': 'Firefox OS',
      'platform': 'Firefox OS',
      'locale': $('#locale').val(),
      'country': $('#country input:radio').val(),
      'manufacturer': $('#device input:radio').val().split('::')[0],
      'device': $('#device input:radio').val().split('::')[1]
    };

    // FIXME - figure out Firefox OS version from Gecko version in UA

    if ($('#email-ok:checked').val()) {
      data['email'] = $('#email-input').val()
    }

    console.log('submitting data');
    console.log(data);

    numCards = $('x-deck')[0].numCards;

    // Here's the order of cards so it's easier to do the math here.
    // email, submitting, thanks, failure
    // -4     -3          -2      -1       numCards
    $('x-deck')[0].shuffleTo(numCards-3);

    var jqxhr = $.post(
      '/api/v1/feedback/', data,
      function(data, textStatus, jqXHR) {
        // on success
        $('x-deck')[0].shuffleTo(numCards-2);
        if (window.localStorage) {
          localStorage.removeItem('emailok');
          localStorage.removeItem('description');
        }
      })
        .fail(function(jqXHR, textStatus, errorThrown) {
          if (window.localStorage) {
            if ($('#email-ok').is(':checked')) {
              localStorage['emailok'] = true;
              console.log('emailok');
            }
            localStorage['description'] = $('#description').val();
          }

          $('x-deck')[0].shuffleTo(numCards-1);
          console.log('submission failure. ' + textStatus + ' ' + errorThrown);
      });
  });

  // populate and set everything up
  if (window.localStorage) {
    if (localStorage['country']) {
      $('#country input:radio').val([localStorage['country']]);
    }
    if (localStorage['device']) {
      $('#device input:radio').val([localStorage['device']]);
    }
    if (localStorage['email']) {
      $('#email-input').val(localStorage['email']);
    }
    if (localStorage['emailok']) {
      $('#email-ok').prop('checked', true);
    }
    if (localStorage['description']) {
      $('#description').val(localStorage['description']);
    }
  }
  $('#email-ok').change();
  $('#email-error').hide();
}

$(init);

})();
