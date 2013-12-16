(function($) {
    // FIXME: Fix this so we don't have to update the JS file every
    // time we update the version map in fjord/base/browsers.py.
    var GECKO_TO_FXOS = {
        '18.0': '1.0',
        '18.1': '1.1',
        '26.0': '1.2',
        '28.0': '1.3'
    };

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

    function countRemaining(inputElement) {
        // Updates the counter and inputElement based on the number of
        // characters in the specified inputElement.
        var $desc = $(inputElement);
        var $counter = $('#' + $desc.attr('id') + '-counter');
        var max = $desc.attr('data-max-length');
        var remaining = max - $desc.val().length;

        $desc.toggleClass('error', remaining < 0);

        $counter.text(remaining);
        $counter.toggleClass('error', remaining < 0);
        $counter.toggleClass('warning', (remaining >= 0 && remaining <= Math.round(max * 0.2)));
    }

    function formReset() {
        $('#email-ok').prop('checked', false);
        $('#description').val('');
        countRemaining($('#description'));

        storageRemoveItem('emailok');
        storageRemoveItem('description');
    }

    /*
     * Infers the FxOS version from the Gecko version in the UA.
     *
     * If this can't find a gecko version in the ua, then it returns
     * null. If this can find a gecko version in the ua, then it tries
     * to map the gecko version to a FxOS version and return that. If it
     * can't, then it returns the Gecko/version.
     *
     * Returns: null, FxOS version or Gecko versoin
     */
    function inferFxosVersion() {
        var gecko_re = /Gecko\/([^\s]+)/,
            possible_version = navigator.userAgent.match(gecko_re);

        if (possible_version != null) {
            possible_version = possible_version[1];
            if (typeof(GECKO_TO_FXOS[possible_version]) !== 'undefined') {
                possible_version = GECKO_TO_FXOS[possible_version];
            } else {
                possible_version = 'Gecko/' + possible_version;
            }
        }

        return possible_version;
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

        countRemaining($('#description'));

        $('#description').on('keyup', function() {
            countRemaining(this);
            if ($('#description').val() === '') {
                $('#description-next-btn').prop('disabled', true);
            } else {
                $('#description-next-btn').prop('disabled', false);
            }
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
            var data, email, jqxhr, version, numCards;

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

            data = {
                'happy': $('#happy').val(),
                'description': $('#description').val(),
                'product': 'Firefox OS',
                'platform': 'Firefox OS',
                'locale': $('#locale').val(),
                'country': $('#country select').val(),
                'device': $('#device select').val()
            };

            version = inferFxosVersion();
            if (version != null) {
                data.version = version;
            }

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
        $('#description-next-btn').prop('disabled', true);
        $('#email-ok').change();
        $('#email-error').hide();
    }

    $(init);

}(jQuery));
