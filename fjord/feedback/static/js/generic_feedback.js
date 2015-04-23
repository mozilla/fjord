(function($, fjord, cards, remoteTroubleshooting, document, window) {
    'use strict';

    $(document).ready(function() {
        window.onpopstate = function(ev) {
            // Switches the the appropriate card
            var pageId = ev.state ? ev.state.page : 'intro';
            cards.changeCard(pageId, false);
        };

        /**
         * Makes the submit button valid/invalid depending on whether
         * the form is valid.
         */
        function toggleSubmitButton() {
            var isValid = true;

            if ($('#description').val().replace(/^\s+/, '') === '' ||
                    $('#description').hasClass('invalid') ||
                    $('#id_url').hasClass('invalid') ||
                    $('#id_email').hasClass('invalid')) {
                isValid = false;
            }

            $('#form-submit-btn').prop('disabled', !isValid);
        }

        fjord.countRemaining($('#description'));

        $('#description').on('input', function() {
            fjord.countRemaining(this);
            if ($(this).val().replace(/^\s+/, '') === '') {
                $(this).addClass('invalid');
            } else {
                $(this).removeClass('invalid');
            }
            toggleSubmitButton();
        });

        $('#id_url').on('input', function() {
            var url = $.trim($(this).val());
            if (fjord.validateUrl(url) || !url.length) {
                $(this).removeClass('invalid');
            } else {
                $(this).addClass('invalid');
            }
            toggleSubmitButton();
        });

        $('#id_email').on('input', function() {
            if (fjord.validateEmail($(this).val())) {
                $(this).removeClass('invalid');
            } else {
                $(this).addClass('invalid');
            }
            toggleSubmitButton();
        });

        /**
         * Selects happy/sad value and switches to the next card.
         *
         * @param {integer} val: 1 if happy, 0 if sad
         */
        function selectHappySad(val) {
            if (val === 1) {
                $('.happy').show();
                $('.sad').hide();
            } else {
                $('.sad').show();
                $('.happy').hide();
            }
            $('#id_happy').val(val);
            // The happy/sad card is the intro card. This changes to
            // the next card in the sequence.
            cards.changeCard('forward');
        }
        $('#happy-button').click(function(ev) {
            selectHappySad(1);
            return false;
        });
        $('#happy-button').keypress(function(ev) {
            if ((ev.keyCode || ev.which) === '13') {
                $('#happy-button').click();
            }
        });
        $('#sad-button').click(function(ev) {
            selectHappySad(0);
            return false;
        });
        $('#sad-button').keypress(function(ev) {
            if ((ev.keyCode || ev.which) === '13') {
                $('#sad-button').click();
            }
        });
        $('#back-button-container').click(function(ev) {
            // We do what the browser back button would do here. We
            // use #back-button-container because svg elements can't
            // do tabindex in Firefox (bug #778654).
            window.history.back();
            return false;
        });
        $('#back-button-container').keypress(function(ev) {
            if ((ev.keyCode || ev.which) === '13') {
                $('#back-button-container').click();
            }
        });
        $('button.next').click(function(ev) {
            cards.changeCard('forward');
            return false;
        });

        $('#email-ok').on('change', function() {
            var checked = $(this).is(':checked');
            $('#id_email').prop('disabled', !checked);
        });

        // If there's a hash and a word, wipe it out with a
        // replaceState.
        if (window.location.hash.match(/^#\w+$/)) {
            window.history.replaceState('', '', '#');
        }

        var browserData;

        // Hide the "browser-ask" section by default. Only show it if
        // the api is there and there's data.
        $('#browser-ask').hide();

        remoteTroubleshooting.available(function (yesno) {
            if (yesno) {
                $('#browser-ask').show();
                remoteTroubleshooting.getData(function (data) {
                    browserData = data;
                    if ($('#browser-ok').is(':checked')) {
                        $('#browser-data').val(JSON.stringify(browserData));
                    }
                });
            }
        });

        $('#browser-ok').on('change', function() {
            var checked = $(this).is(':checked');
            if (checked && browserData) {
                $('#browser-data').val(JSON.stringify(browserData));
            } else {
                $('#browser-data').val('{}');
            }
        });

        // Switch to the intro card
        cards.changeCard('intro', false);

        // Handle pre-filled variables which could have the
        // side-effect of switching cards, so we should do this last
        var qs = fjord.getQuerystring();
        if (qs.happy) {
            if (qs.happy === '0') {
                selectHappySad(0);
            } else if (qs.happy === '1') {
                selectHappySad(1);
            }
        }
    });
}(jQuery, fjord, cards, remoteTroubleshooting, document, window));
