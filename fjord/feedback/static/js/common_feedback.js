(function($) {
    var formName = $('body').data('form-name');

    if (!formName) {
        if (console) {
            console.log('Missing data-form-name on <body/>.');
        }
        return;
    }

    document.addEventListener('DOMComponentsLoaded', function setupAnalyticsAndStuff() {
        // UNSUBSCRIBE!
        document.removeEventListener('DOMComponentsLoaded', setupAnalyticsAndStuff);

        var xdeck = $('x-deck')[0];

        // Go to the first card.
        xdeck.showCard(0);

        // Fire off a GA event for the first card.
        // NOTE: I really wanted to setup the event listener first,
        // then switch to the first card. But that isn't working for
        // whatever reason. So I fire off the first GA event manually
        // here.
        if (_gaq) {
            _gaq.push(['_trackEvent', 'FeedbackFlow', formName + '-' + xdeck.cards[0].id]);
        }

        // Listen to the show event of the x-cards.
        xtag.addEvent(document, 'show:delegate(x-card)', function(obj) {
            // Fire off GA event when each new card is shown.
            if (_gaq) {
                _gaq.push(['_trackEvent', 'FeedbackFlow', formName + '-' + this.id]);
            }
        });
    });
}(jQuery));
