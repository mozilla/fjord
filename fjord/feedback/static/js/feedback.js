(function($) {
    $.extend($.fn, {
        nodeIndex: function() {
            var i = -1, node = this.get(0);
            for ( ; node; i++, node = node.previousSibling);
            return i;
        },

        switchTo: function(what, callback) {
            var fromElem = this;
            var fromEnd;
            var fromStart;
            var toElem = $(what);
            var width = $(window).width();

            if (fromElem.nodeIndex() < toElem.nodeIndex()) {
                fromEnd = -width;
                toStart = width;
            } else {
                fromEnd = width;
                toStart = -width;
            }

            fromElem.css({ left: 0, right: 0 });
            toElem.addClass('entering')
                .css({ left: toStart, right: -toStart, display: 'block' });
            $('html').addClass('transitioning');

            toElem.one('transitionend', function(e) {
                fromElem.css({ display: 'none' });
                toElem.removeClass('entering');
                $('html').removeClass('transitioning');
                if (callback) callback();
            });

            setTimeout(function() {
                fromElem.css({ left: fromEnd, right: -fromEnd });
                toElem.css({ left: 0, right: 0 });
            }, 100);

            return this;
        },
        submitButton: function(state) {
            var textElem = this.find('span');
            var oldHTML = textElem.html();
            var newTextAttr = (state == 'waiting') ? 'data-waittext' : 'data-text';

            this.toggleClass('waiting', state == 'waiting');
            textElem.html( this.attr(newTextAttr) );

            if (state == 'waiting') this.attr('data-text', oldHTML);

            return this;
        },
        clickEnable: function(bindTo) {
            return this.each(function() {
                onClick.call(this);
                $(this).click(onClick);
            });

            function onClick() {
                var checked = this.checked;
                $(bindTo)[0].disabled = !checked;
            }
        }
    });


    var currentArticle;

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

    function getArticle(href) {
        var hash = (href || '').replace(/^.*#/, '') || 'intro',
            validhashes = ['intro', 'happy', 'sad'];
        // If passed an invalid hash, go to the intro.
        if (-1 === validhashes.indexOf(hash.toLowerCase())) {
            hash = 'intro';
        }
        var elem = $('#'+hash);
        return elem.length ? elem : $('#intro');
    }

    function goToArticle(href, pushState, callback)
    {
        var oldArticle = currentArticle;
        var newArticle = getArticle(href);

        if (oldArticle.get(0) == newArticle.get(0)) {
            return;
        }

        if (pushState) window.history.pushState('', '', '#' + newArticle.attr('id'));
        currentArticle = newArticle;

        oldArticle.switchTo(newArticle, callback);
    }

    function init() {
        // Look for errors and show that initially
        var errorlst = $('article .errorlist');
        if(errorlst.length) {
            currentArticle = errorlst.closest('article');
            currentArticle.css({ display: 'block' });
            window.location.hash = currentArticle.attr('id');
        } else {
            currentArticle = getArticle(document.location.hash);
            currentArticle.css({ display: 'block' });
        }

        window.onpopstate = function(e) {
            goToArticle(document.location.hash);
        };

        $('.submit a').click(function(e) {
            if ($(this).hasClass('disabled') === false) {
                $(this).addClass('disabled');
                $(this).closest('form').submit();
            }

            return false;
        });

        $('article form').submit(function(e) {
            var button = $(this).find('.submit a');
            button.submitButton('waiting');
        });

        $('article textarea').each(function(i, element) {
            countRemaining(element);
        });
        $('article textarea').keyup(function() {
            countRemaining(this);
        });

        $('#happy-with-url').clickEnable('#happy-url');
        $('#sad-with-url').clickEnable('#sad-url');

        function email_expansion(elem, time) {
            var checked = $(elem).prop('checked');
            var email = $(elem).parents('label').siblings('.email');

            if (checked) {
                email.show(time);
            } else {
                email.hide(time);
            }
        }

        $('.email-ok input[type=checkbox]').on('change', function() {
            email_expansion(this, 300);
        }).each(function() {
            email_expansion(this, 0);
        });

        $('html').addClass('js');
    };

    $(init);

}(jQuery));
