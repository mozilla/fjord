/* general initialization */
$(document).ready(function(){
    // Set up input placeholders.
    $('input[placeholder]').placeholder();

    // Submit on locale/channel choice
    $('form.languages,form.channels')
        .find('select').change(function(){
            this.form.submit();
        }).end()
        .find('button').hide();

    // Open twitter links as popup
    $('.messages .options a.twitter,a.tweet-this').live('click', function(e) {
        var x = Math.max(0, (screen.width - 550) / 2),
            y = Math.max(0, (screen.height - 450) / 2);
        window.open($(this).attr('href'), 'tweetthis',
            'height=450,width=550,left='+x+',top='+y);

        return false;
    });

    // Allow elements to have a close button
    $('.close-button').live('click', function(e) {
        $(this).parent().fadeOut(300, function() { $(this).remove(); });
    });
});

/* Fake the placeholder attribute since Firefox doesn't support it.
 * (Borrowed from Zamboni) */
jQuery.fn.placeholder = function() {
    /* Bail early if we have built-in placeholder support. */
    if ('placeholder' in document.createElement('input')) {
        return this;
    }
    return this.focus(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == text) {
            $this.val('').removeClass('placeholder');
        }
    }).blur(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() === '') {
            $this.val(text).addClass('placeholder');
        }
    }).each(function(){
        /* Remove the placeholder text before submitting the form. */
        var self = $(this);
        self.closest('form').submit(function() {
            if (self.hasClass('placeholder')) {
                self.val('');
            }
        });
    }).blur();
};

/* Python(ish) string formatting:
* >>> format('{0}', ['zzz'])
* "zzz"
* >>> format('{x}', {x: 1})
* "1"
*/
function format(s, args) {
    var re = /\{([^}]+)\}/g;
    return s.replace(re, function(_, match){ return args[match]; });
}
