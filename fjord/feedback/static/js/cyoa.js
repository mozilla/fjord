(function($) {
    document.addEventListener('DOMComponentsLoaded', function firstCard() {
        var xdeck = $('x-deck')[0];
        document.removeEventListener('DOMComponentsLoaded', firstCard);
        xdeck.showCard(0);
    });

}(jQuery));
