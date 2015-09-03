(function(window, $) {
    'use strict';
    $(window.document).ready(function() {
        /**
         * Removes existing match data
         */
        function reset() {
            $('#matched-feedback').empty();
        }

        /**
         * Indicate start of work.
         */
        function startWork() {
            $('#matched-working').removeClass('hidden');
        }

        /**
         * Indicate end of work.
         */
        function endWork() {
            $('#matched-working').addClass('hidden');
        }

        /**
         * Add count to the page.
         *
         * @param {Integer} The number of matches.
         */
        function addCount(count) {
            $('#matched-feedback').append('<div>There were ' + count + ' matches.</div>');
        }

        /**
         * Add a match to the page.
         *
         * @param {Object} The match data.
         */
        function addMatch(data) {
            // Convert happy to a word which we use for text and html class
            data.happy = data.happy ? 'happy' : 'sad';
            // start and end are YYYY-MM-DD dates
            data.end = data.created.slice(0, 10);
            data.start = data.created.slice(0, 10);
            // Truncate description
            // Note: This sucks because it might not contain the part that matches,
            // but if that's the case, they can click on the permalink and see the
            // whole thing.
            if (data.description.length > 200) {
                data.description = data.description.slice(0, 200) + '....';
            }
            var template = (
                '<div id="feedback-{{id}}" class="opinion"> ' +
                '<span class="sprite {{happy}}">{{happy}}</span> ' +
                '<p class="desc"></p> ' +
                '<ul class="meta"> ' +
                '<li><a href="/?date_end={{end}}&date_start={{start}}">{{created}}</a></li> ' +
                '<li><a href="/?product={{product}}">{{product}}</a> <a href="/?product={{product}}&version={{version}}">{{version}}</a></li> ' +
                '<li><a href="/?platform={{platform}}">{{platform}}</a> ' +
                '<li><a href="/?locale={{locale}}">{{locale}}</a> ' +
                '<li><a href="/dashboard/response/{{id}}">permalink</a> ' +
                '</ul> ' +
                '</div>'
            );
            template = template.replace(/(\{\{\w*\}\})/g,
                                        function(match, key) {
                                            return data[key.slice(2, -2)];
                                        });

            $('#matched-feedback').append(template);
            // Add the description in a way that escapes it.
            $('#feedback-' + data.id + ' .desc').text(data.description);
        }

        /**
         * Pulls out trigger rule data, package it in JSON and send it
         * to Input to get the list of recent matches.
         *
         * @returns {Promise} A promise for the response
         */
        function apiCall(data) {
            var jqxhr = $.ajax({
                type: 'POST',
                url: '/api/v1/analytics/triggerrule/match/',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                },
                data: JSON.stringify(data),
                dataType: 'json'
            });

            return jqxhr.promise();
        }

        /**
         * Pulls values from form, sets up data, performs API call and when
         * that returns, generates the matches on the page.
         */
        function getMatches() {
            var data = {
                locales: $('#id_locales').val().split('\n'),
                products: [],
                versions: $('#id_versions').val().split('\n'),
                keywords: $('#id_keywords').val().split('\n'),
                url_exists: null
            };
            // product is in a select and we want the text--not the value.
            var productVals = $('#id_products').val();
            if (productVals !== null && productVals.length > 0) {
                var productOptions = $('#id_products option');
                data.products = productVals.map(function(index) {
                    index = parseInt(index, 10) - 1;
                    return productOptions[index].text;
                });
            }

            // url_exists is in a select and we want either null, true or
            // false--not the value.
            var urlExistsVals = $('#id_url_exists').val();
            var urlExistsOptions = $('#id_url_exists option');
            var urlExistsName = urlExistsOptions[parseInt(urlExistsVals[0], 10) - 1].text;
            if (urlExistsName === 'Unknown') {
                data.url_exists = null;
            } else if (urlExistsName === 'Yes') {
                data.url_exists = true;
            } else {
                data.url_exists = false;
            }

            startWork();
            apiCall(data)
                .then(function (matches) {
                    addCount(matches.count);
                    matches.results.map(addMatch);
                    endWork();
                })
                .fail(function () {
                    window.alert('Unknown error when fetching matches. Sorry this is unhelpful.');
                    endWork();
                });
        }

        $('button.testBtn').on('click', function() {
            reset();
            getMatches();
            return false;
        });
    });
}(window, jQuery));
