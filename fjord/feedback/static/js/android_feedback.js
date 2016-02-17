(function($) {
  'use strict';

  // Settings
  var browserReviewUrl = 'https://play.google.com/store/apps/details?id=org.mozilla.CHANNEL#details-reviews';
  var deviceReviewUrl = 'market://details?id=org.mozilla.CHANNEL';

  // Initialize
  var reviewUrl = '';
  var lastUrl = '';
  var url = decodeURI(window.location.href);

  /*
    Decide whether they're here deliberately or due to a feedback prompt
    (Fx Android's feedback prompt includes a utm param);
  */
  var fromDevice = /source=feedback-prompt/.test(url);
  if (fromDevice) {
    reviewUrl = deviceReviewUrl;
    /* If client prompted for feedback, delegate some event handling to the client */
    $(document).on('click', '#maybe-later, #no-thanks', function(e) {
        e.preventDefault();
        var eventName = this.getAttribute('data-event');
        var feedbackEvent = new Event(eventName, {"bubbles":true, "cancelable":false});
        this.dispatchEvent(feedbackEvent);
    });
  }
  else {
    reviewUrl = browserReviewUrl;
    // If browsed here deliberately, no need for these
    $('#maybe-later, #no-thanks').hide();
  }

  // Decide what product they might review on play store
  var version = $('body').attr('data-version');
  var channel = $('body').attr('data-channel');
  if (channel == 'beta') {
    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox_beta');
  }
  else if (channel != '' && /^(?!(beta|release)).*$/.test(channel)) {
    // If they specify a channel not in play store, don't encourage review
    $('.happy .message-box').hide();
  }
  else {
    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox');
  }

  $('#play-store').attr('href', reviewUrl);

  // if they say don't send url in sad feedback, don't send url
  var $id_url = $('#id_url').first();
  $('#last-checkbox').click(function(e) {
    if (this.checked) {
      $id_url.val(lastUrl).prop('disabled', false);
    }
    else {
      lastUrl = $('#id_url').val();
      $id_url.val('').prop('disabled', 'disabled');
    }
  });

}(jQuery));
