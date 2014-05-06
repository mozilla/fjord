window.fjord = window.fjord || {};

(function() {
    /*
     * Validates a string as an email address
     */
    fjord.validateEmail = function(text) {
        var emailRegExp = /^[a-zA-Z0-9._\-\+]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}$/;
        if (text.length > 0 && text.match(emailRegExp)) {
            return true;
        }
        return false;
    };
}());
