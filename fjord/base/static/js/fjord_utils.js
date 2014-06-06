window.fjord = window.fjord || {};

(function() {
    /**
     * Validates a string as an email address
     * @param {string} text - The text we're validating.
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
     * @returns {string}
     */
    fjord.format = function(s, args) {
        var re = /\{([^}]+)\}/g;
        return s.replace(re, function(_, match){ return args[match]; });
    };

    /**
     * Returns the current query string as a JavaScript object.
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
}());
