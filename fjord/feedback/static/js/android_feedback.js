(function($) {
  'use strict';

  // settings
  var browserReviewUrl = 'https://play.google.com/store/apps/details?id=org.mozilla.CHANNEL#details-reviews';
  var deviceReviewUrl = 'market://details?id=org.mozilla.CHANNEL';

  // initialize
  var reviewUrl, lastUrl = '';
  var url = decodeURIComponent(window.location.href);


  /*
    Decide whether they're on Fx Android or not
    (Fx Android's feedback prompt includes a utm param)
  */
  var fromDevice = /source=feedback-prompt/.test(url);
  if (fromDevice) {
    reviewUrl = deviceReviewUrl;
    /* 
      TODO: When bug 1237388 is resolved, remove #play-store here.
      If url params are as assumed below, it'll Just Work(tm)!
    */
    $('#maybe-later, #no-thanks, #play-store').click(
      function(e) {
        e.preventDefault();
        var feedbackEvent = document.createEvent('Events');
        feedbackEvent.initEvent(this.getAttribute('data-event'), true, false);
        this.dispatchEvent(feedbackEvent);
      }
    );
  }
  else {
    reviewUrl = browserReviewUrl;
    // if browsed here deliberately, no need for these
    $('#maybe-later, #no-thanks').hide();
  }

  // decide what product they might review on play store
  var version = $('body').attr('data-version');
  var channel = $('body').attr('data-channel');
  if (channel == 'beta') {
    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox_beta');
  }
  else if (channel != '' && /^(?!(beta|release)).*$/.test(channel)) {
    // if they specify a channel not in play store, don't encourage review
    $('.happy .message-box').hide();
  }
  else {
    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox');
  }

  $('#play-store').attr('href', reviewUrl);

  // if they say don't send url in sad feedback, don't send url
  $('#last-checkbox').click(function(e) {
    if (this.checked) {
      $('#id_url').val(lastUrl).prop('disabled', false);
    }
    else {
      lastUrl = $('#id_url').val();
      $('#id_url').val('').prop('disabled', 'disabled');
    }
  });

}(jQuery));
