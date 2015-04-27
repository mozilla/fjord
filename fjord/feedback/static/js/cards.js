/**
 * cards expects:
 *
 * - all cards are divs with class "card"
 * - inactive cards have the "inactive" class; when starting out
 *   all cards should be marked inactive but the first one
 * - the back button has the "back-button-container" class
 * - data-focus attribute on the card has the id of the element
 *   that should receive focus
 * - header -> h1 gets the value of the data-title attribute on
 *   the card
 */
window.cards = window.cards || {};

(function($, cards) {
    'use strict';

    cards.getCardIds = function() {
        return $('.card')
            .map(function() {
                return this.id;
            })
            .get();
    };

    /**
     * Retrieve the id of the next card in the sequence.
     *
     * Note: This is not forgiving of errors.
     */
    cards.getNext = function(id) {
        var cardIds = cards.getCardIds();
        return cardIds[cardIds.indexOf(id)+1];
    };

    /**
     * Retrieve the id of the previous card in the sequence.
     *
     * Note: This is not forgiving of errors.
     */
    cards.getPrevious = function(id) {
        var cardIds = cards.getCardIds();
        return cardIds[cardIds.indexOf(id)-1];
    };

    /**
     * Returns the Id of the currently showing card.
     */
    cards.getCurrent = function() {
        return $('.card:not(.inactive)').attr('id');
    };

    /**
     * Switches to the card with specified id or to the next or
     * previous card when specifying "forward" or "reverse". This also
     * updates the window history via pushState if updateHistory is
     * true.
     *
     * @param {string} cardId: Id of the card to switch to or "forward"
     *     or "reverse".
     * @param {boolean} updateHistory: Whether or not to update
     *     the window.history. Defaults to true.
     */
    cards.changeCard = function(cardIdOrDirection, updateHistory) {
        var cardId = null;

        if (updateHistory === undefined) {
            updateHistory = true;
        }

        if (cardIdOrDirection === 'forward') {
            cardId = cards.getNext(cards.getCurrent());
        } else if (cardIdOrDirection === 'reverse') {
            cardId = cards.getPrevious(cards.getCurrent());
        } else {
            cardId = cardIdOrDirection;
        }

        // Make active card inactive
        $('.card:not(.inactive)').addClass('inactive');

        // Set title, add back-button, make new card active
        var $card = $('#' + cardId);
        $('header h1').text($card.attr('data-title'));
        if ($card.hasClass('no-back')) {
            $('#back-button-container').hide();
        } else {
            $('#back-button-container').show();
        }
        $card.removeClass('inactive');
        if ($card.attr('data-focus') !== undefined) {
            $($card.attr('data-focus')).focus();
        }
        if (updateHistory) {
            window.history.pushState({page: cardId}, '', '#' + cardId);
        }
    };
}(jQuery, cards));
