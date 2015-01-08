window.fjord = window.fjord || {};

(function($, fjord, document) {
    'use strict';

    /**
     * Validates a string as an email address.
     *
     * @param {string} text - The string to validate.
     *
     * @returns {boolean}
     */
    fjord.validateEmail = function(text) {
        var emailRegExp = /^[a-zA-Z0-9._\-\+]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}$/;
        if (text.length > 0 && text.match(emailRegExp)) {
            return true;
        }
        return false;
    };

    /**
     * Python(ish) string formatting:
     *
     *     >>> format('{0}', ['zzz'])
     *     "zzz"
     *     >>> format('{x}', {x: 1})
     *     "1"
     *
     * @param s {string} - The string to interpolate.
     * @param args {varies} - The arguments to interpolate into the string.
     *
     * @returns {string}
     */
    fjord.format = function(s, args) {
        var re = /\{([^}]+)\}/g;
        return s.replace(re, function(_, match){ return args[match]; });
    };

    /**
     * Returns the current query string as a JavaScript object.
     *
     * @returns {Object}
     */
    fjord.getQuerystring = function() {
        var qs = window.location.search;
        var parsed = {};
        var i;

        if (qs.length) {
            // Remove '?'
            qs = qs.slice(1);
            var opts = qs.split('&');
            for (i=0; i < opts.length; i++) {
                var opt = opts[i].split('=');
                console.log(opts[i]);
                console.log(opt);
                parsed[opt[0]] = opt[1];
            }
        }

        return parsed;
    };

    /**
     * Sets the querystring to the args specified.
     */
    fjord.setQuerystring = function(args) {
        var parts = [];
        var total_obj = {};
        var i, key, value;

        for (i=0; i < arguments.length; i++) {
            for (key in arguments[i]) {
                value = arguments[i][key];
                total_obj[key] = value;
            }
        }
        for (key in total_obj) {
            value = total_obj[key];
            if (value !== undefined) {
                parts.push(fjord.format('{0}={1}', [key, value]));
            }
        }
        window.location.search = '?' + parts.join('&');
    };

    /**
     * Detect browser <input type="date" ...> support.
     *
     * @returns {boolean}
     */
    fjord.isDateInputSupported = function() {
        var input = document.createElement('input');
        input.setAttribute('type','date');
        var notADateValue = 'not-a-date';
        input.setAttribute('value', notADateValue);

        return input.value !== notADateValue;
    };

    /**
    * Validates a URL.
    *
    * @param {string} url - The url we're validating.
    *
    * @returns {boolean}
    */
    fjord.validateUrl = function(url) {
        if (url.length > 0) {
            var aboutUrlRegExp = /^about:/;
            var chromeUrlRegExp = /^chrome:\/\//;
            var urlRegExp = /^((ftp|http|https):\/\/)?(\w+:{0,1}\w*@)?(\S+\.\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?$/;

            if (urlRegExp.test(url) ||
                    aboutUrlRegExp.test(url) ||
                    chromeUrlRegExp.test(url)) {
                return true;
            }
        }
        return false;
    };

    /**
     * Updates related character counter for a inputElement (text)
     * with correct count.
     *
     * The id for the related character counter must be the id
     * of the inputElement with "-counter" appended to it.
     *
     * The character count max is the "data-max-length" property of
     * the inputElement.
     *
     * If the number of characters is beyond the data-max-length, then
     * it adds the "error" class to the inputElement.
     *
     * If the number of characters is beyond 80% of the
     * data-max-length, then it adds the "warning" class to the
     * inputElement.
     *
     * @param {elem} inputElement - The element to count characters of.
     */
    fjord.countRemaining = function(inputElement) {
        var $desc = $(inputElement);
        var $counter = $('#' + $desc.attr('id') + '-counter');
        var max = $desc.attr('data-max-length');
        var remaining = max - $desc.val().replace(/\s+/, '').length;

        $desc.toggleClass('error', remaining < 0);

        $counter.text(remaining);
        $counter.toggleClass('error', remaining < 0);
        $counter.toggleClass('warning', (remaining >= 0 && remaining <= Math.round(max * 0.2)));
    };
}(jQuery, window.fjord, document));
