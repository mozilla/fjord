(function() {
function storageAddItem(key, val) {
  if (window.localStorage) {
    localStorage[key] = val;
  }
}

function storageRemoveItem(key) {
  if (window.localStorage) {
    localStorage.removeItem(key);
  }
}

function storageItem(key) {
  if (window.localStorage) {
    return localStorage[key];
  }
}

function formReset() {
  $('#email-ok').prop('checked', false);
  $('#description').val('');

  storageRemoveItem('emailok');
  storageRemoveItem('description');
}

function init() {
  var xdeck = $('x-deck')[0];

  $('#intro').on('click', 'button', function() {
    var happy = $(this).hasClass('happy');

    $('#moreinfo')
          .removeClass(happy ? 'sad' : 'happy')
          .addClass(happy ? 'happy' : 'sad');
    $('#happy').val(happy ? '1' : '0');
    xdeck.shuffleNext();
  });

  $('button.back').on('click', function() {
    xdeck.shufflePrev();
  });

  $('button.next').on('click', function() {
    xdeck.shuffleNext();
  });

  $('#country select').on('change', function(ev) {
    storageAddItem('country', $('#country select').val());
  });

  $('#device select').on('change', function() {
    storageAddItem('device', $('#device select').val());
  });

  $('#email .email-ok input').on('change', function() {
    var on = $(this).is(':checked');
    $('#email .email').toggle(on);
    $('#privacy-email').toggle(on);
  });

  $('button.cancel').on('click', function() {
    formReset();
    xdeck.shuffleTo(0);
  });

  $('button.complete').on('click', function() {
    var data, device, email, jqxhr, numCards;

    // verify email address
    if ($('#email-ok').is(':checked')) {
      email = $.trim($('#email-input').val());

      if (email !== '') {
        // this should be close enough to what django is doing that we
        // can catch issues client-side
        if (!email.match(/^[a-zA-Z0-9._\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}$/)) {
          $('#email-error').show();
          return;
        }
      }

      // in case it was showing, we hide it again
      $('#email-error').hide();

      storageAddItem('email', $('#email-input').val());
    }

    device = $('#device select').val().split('::');

    data = {
      'happy': $('#happy').val(),
      'description': $('#description').val(),
      'product': 'Firefox OS',
      'platform': 'Firefox OS',
      'locale': $('#locale').val(),
      'country': $('#country select').val(),
      'manufacturer': device[0],
      'device': device[1]
    };

    // FIXME - figure out Firefox OS version from Gecko version in UA

    if ($('#email-ok:checked').val() && email !== '') {
      data.email = $('#email-input').val();
    }

    numCards = xdeck.numCards;

    // here's the order of cards so it's easier to do the math here.
    // email, submitting, thanks, failure, tryagain
    // -5     -4          -3      -2       -1       numCards
    xdeck.shuffleTo(numCards-4);

    jqxhr = $.ajax({
      contentType: 'application/json',
      data: JSON.stringify(data),
      dataType: 'json',
      type: 'POST',
      url: '/api/v1/feedback/',
      success: function(data, textStatus, jqxhr) {
        formReset();
        xdeck.shuffleTo(numCards-3);
      },
      error: function(jqxhr, textStatus, errorThrown) {
        // persist state so they can try again later
        if ($('#email-ok').is(':checked')) {
          storageAddItem('emailok', true);
        }
        storageAddItem('description', $('#description').val());

        xdeck.shuffleTo(numCards-2);
        // FIXME - get the error message which is in the response body
        console.log('submission failure. ' + textStatus + ' ' + errorThrown);
      }});
  });

  // populate and initialize values to what was persisted
  if (storageItem('country')) {
    $('#country select').val(storageItem('country'));
  }
  if (storageItem('device')) {
    $('#device select').val(storageItem('device'));
  }
  if (storageItem('email')) {
    $('#email-input').val(storageItem('email'));
  }

  if (storageItem('emailok')) {
    $('#email-ok').prop('checked', true);
  }
  if (storageItem('description')) {
    $('#description').val(storageItem('description'));

    document.addEventListener('DOMComponentsLoaded', function() {
      // if there's a description, this indicates that the previous
      // attempt to submit failed so we go directly to the "try
      // again" card; have to do it in this listener because
      // otherwise x-deck isn't ready, yet
      var numCards = xdeck.numCards;
      xdeck.shuffleTo(numCards-1);
    });
  }
  $('#email-ok').change();
  $('#email-error').hide();
}

$(init);

}());
