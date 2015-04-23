(function($, fjord, cards, localStorage, document, window, navigator) {
    'use strict';

    $(document).ready(function() {
        // FIXME: Fix this so we don't have to update the JS file every
        // time we update the version map in fjord/base/browsers.py.
        var GECKO_TO_FXOS = {
            '18.0': '1.0',
            '18.1': '1.1',
            '26.0': '1.2',
            '28.0': '1.3'
        };

        /*
         * Infers the FxOS version from the Gecko version in the UA.
         *
         * If this can't find a gecko version in the ua, then it returns
         * null. If this can find a gecko version in the ua, then it tries
         * to map the gecko version to a FxOS version and return that. If it
         * can't, then it returns the Gecko/version.
         *
         * @returns: null, FxOS version or Gecko version
         */
        function inferFxosVersion() {
            var gecko_re = /Gecko\/([^\s]+)/,
                possible_version = navigator.userAgent.match(gecko_re);

            if (possible_version !== null) {
                possible_version = possible_version[1];
                if (typeof(GECKO_TO_FXOS[possible_version]) !== 'undefined') {
                    possible_version = GECKO_TO_FXOS[possible_version];
                } else {
                    possible_version = 'Gecko/' + possible_version;
                }
            }

            return possible_version;
        }

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

        window.onpopstate = function(ev) {
            // Switches the the appropriate card
            var pageId = ev.state ? ev.state.page : 'intro';
            cards.changeCard(pageId, false);
        };

        function formReset() {
            $('#email-ok').prop('checked', false);
            $('#description').val('');
            fjord.countRemaining($('#description'));

            storageRemoveItem('emailok');
            storageRemoveItem('description');
        }

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
            $('#happy').val(val);
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

        $('#country select').on('change', function(ev) {
            storageAddItem('country', $('#country select').val());
        });
        $('#device select').on('change', function() {
            storageAddItem('device', $('#device select').val());
        });

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

        $('#email-ok').on('change', function() {
            var checked = $(this).is(':checked');
            $('#id_email').prop('disabled', !checked);
        });

        $('button.cancel').on('click', function() {
            formReset();
            cards.changeCard('intro');
        });

        $('button.complete').on('click', function() {
            var data, email, jqxhr, version, numCards;

            // verify email address
            if ($('#email-ok').is(':checked')) {
                email = $.trim($('#id_email').val());

                if (email !== '') {
                    if (!fjord.validateEmail(email)) {
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
                'device': $('#device select').val(),
                'url': $.trim($('#id_url').val()),
                'user_agent': navigator.userAgent
            };

            version = inferFxosVersion();
            if (version !== null) {
                data.version = version;
            }

            if ($('#email-ok:checked').val() && email !== '') {
                data.email = $.trim($('#id_email').val());
            }

            // Grab the source and campaign from the querystring if
            // available.
            var qs = fjord.getQuerystring();
            if (qs.utm_source) {
                data.source = decodeURI(qs.utm_source);
            }
            if (qs.utm_campaign) {
                data.campaign = decodeURI(qs.utm_campaign);
            }

            cards.changeCard('submitting', false);

            jqxhr = $.ajax({
                contentType: 'application/json',
                data: JSON.stringify(data),
                dataType: 'json',
                type: 'POST',
                url: '/api/v1/feedback/',
                success: function(data, textStatus, jqxhr) {
                    formReset();
                    cards.changeCard('thanks', false);
                },
                error: function(jqxhr, textStatus, errorThrown) {
                    // persist state so they can try again later
                    if ($('#email-ok').is(':checked')) {
                        storageAddItem('emailok', true);
                    }
                    storageAddItem('description', $('#description').val());

                    cards.changeCard('failure', false);
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
        $('#email-error').hide();

        // Switch to the tryagain card or the intro card depending on
        // whether we've detected that they're in the middle of
        // feedback or not.
        if (storageItem('description')) {
            $('#description').val(storageItem('description'));
            cards.changeCard('tryagain', false);
        } else {
            cards.changeCard('intro', false);
        }
    });

}(jQuery, fjord, cards, localStorage, document, window, navigator));
