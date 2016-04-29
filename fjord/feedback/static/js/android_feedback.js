(function ($, cards) {
    'use strict';

    $(document).ready(function() {

        // Settings
        var browserReviewUrl = 'https://play.google.com/store/apps/details?id=org.mozilla.CHANNEL#details-reviews';
        var deviceReviewUrl = 'market://details?id=org.mozilla.CHANNEL';

        // Initialize
        var reviewUrl = browserReviewUrl;
        var channel = $('body').attr('data-channel');

        /*
          Fx Android fires an event when loaded by feedback prompt;
          in that case act like we're on a device.

          Simulate this in the console: Services.obs.notifyObservers(null, "Feedback:Show", null);
        */
        document.addEventListener('FeedbackPrompted', function(event) {
            reviewUrl = deviceReviewUrl;
            $('a.maybe-later, a.no-thanks').show();

            // If client prompted for feedback, delegate some event handling to the client
            $(document).on('click', 'a.maybe-later, a.no-thanks', function(e) {
                e.preventDefault();
                var eventName = this.getAttribute('data-event');
                var feedbackEvent = new Event(eventName, {'bubbles':true, 'cancelable':false});
                this.dispatchEvent(feedbackEvent);
            });
        });

        $(document).on('click', '#happy-button-android', function(e) {
          // Play store only has beta/release
            if (channel != '' && /^(beta|release).*$/.test(channel)) {
                if (channel == 'beta') {
                    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox_beta');
                }
                else {
                    reviewUrl = reviewUrl.replace('CHANNEL', 'firefox');
                }
                $('#play-store').attr('href', reviewUrl);
            }
            else {
                // If not beta/release, hide CTA to review on play store
                $('.play-store-cta').hide();
            }

            $('.happy').show();
            $('.sad').hide();
            cards.changeCard('forward');
            return false;
        });

        $(document).on('keypress', '#happy-button-android', function(e) {
            if ((e.keyCode || e.which) === '13') {
                $('#happy-button-android').click();
            }
        });

    });
}(jQuery, cards));
