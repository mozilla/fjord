(function($) {
    var xdeck = $('x-deck')[0];

    function goNext() {
        // Moves to the next card and updates history.
        var oldIndex = xdeck.selectedIndex;
        xdeck.nextCard();
        window.history.pushState({page: xdeck.selectedIndex}, '', '#' + xdeck.selectedIndex);
    }

    window.onpopstate = function(ev) {
        // Switches the the appropriate card
        var pageId = ev.state ? ev.state.page : 0;
        if (pageId >= 0 && pageId < xdeck.cards.length) {
            xdeck.showCard(pageId);
        }
    };

    function countRemaining(inputElement) {
        // Updates the counter and inputElement based on the number of
        // characters in the specified inputElement.
        var $desc = $(inputElement);
        var $counter = $('#' + $desc.attr('id') + '-counter');
        var max = $desc.attr('data-max-length');
        var remaining = max - $desc.val().replace(/\s+/, '').length;

        $desc.toggleClass('error', remaining < 0);

        $counter.text(remaining);
        $counter.toggleClass('error', remaining < 0);
        $counter.toggleClass('warning', (remaining >= 0 && remaining <= Math.round(max * 0.2)));
    }

    function toggleNextButton(id) {
        // Toggles the enabling of the next button
        // id is the id of the button we want to affect
        var isValid = true;
        if (id == 'description-next-btn') {
            // Check if the description and url fields are valid
            if ($('#description').hasClass('invalid') ||
                    $('#id_url').hasClass('invalid')) {
                isValid = false;
            }
        }

        if (isValid) {
            $('#'+id).prop('disabled', false);
        } else {
            $('#'+id).prop('disabled', true);
        }
    }

    function init() {
        $('input[type="text"]').keypress(function(event) {
            // Tweak handling for CR for input text fields so they go
            // to the next card or, if on the last card, submit the
            // form.
            if (event.which == 13) {
                if (xdeck.selectedIndex < (xdeck.cards.length - 1)) {
                    // If it's not on the last card, nextCard().
                    goNext();
                } else {
                    // It's on the last card, so we submit the form.
                    $('button.complete').click();
                }
                return false;
            }
        });

        $('#intro button').click(function(event) {
            var happy = $(this).hasClass('happy');

            $('#moreinfo')
                .removeClass(happy ? 'sad' : 'happy')
                .addClass(happy ? 'happy' : 'sad');
            $('#id_happy').val(happy ? '1' : '0');
            goNext();
            return false;
        });

        $('button.back').click(function(event) {
            // We do what the browser back button would do here
            window.history.back();
            return false;
        });

        $('button.next').click(function(event) {
            goNext();
            return false;
        });

        countRemaining($('#description'));

        $('#description').on('input', function() {
            countRemaining(this);
            if ($(this).val().replace(/^\s+/, '') === '') {
                $(this).addClass('invalid');
            } else {
                $(this).removeClass('invalid');
            }
            toggleNextButton('description-next-btn');
        });

        $('#id_url').on('input', function() {
            var urlRegExp = /^(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?$/;
            if ($(this).val().length > 0 &&
                    !$(this).val().match(urlRegExp)) {
                $(this).addClass('invalid');
            } else {
                $(this).removeClass('invalid');
            }
            toggleNextButton('description-next-btn');
        });

        $('#email-ok').on('change', function() {
            var on = $(this).is(':checked');
            $('#email-details').toggle(on);
        });

        $('button.complete').click(function(event) {
            var data, email, numCards;

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
            }

            // Lack of 'return false;' here submits the form.
        });

        // If there's a hash and a number, wipe it out with a
        // replaceState.
        if (window.location.hash.match(/^#\d+$/)) {
            window.history.replaceState('', '', '#');
        }

        // Toggle the email-ok off.
        $('#email-ok').change();

        // Disable the "next" button on the details card. It gets
        // re-enabled when they've started typing.
        $('#description-next-btn').prop('disabled', true);
    }

    $(init);

}(jQuery));
