var _gaq = _gaq || [];
_gaq.push(['_setAccount', 'UA-35433268-26']);

// Add any extra pushes from body[data-ga-push].
var extraPush = $('body').data('ga-push');
if (extraPush && extraPush.length) {
  for (var i = 0, l = extraPush.length; i < l; i++) {
    _gaq.push(extraPush[i]);
  }
}

_gaq.push(['_trackPageview']);

(function() {
    var ga = document.createElement('script');
    ga.type = 'text/javascript';
    ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(ga, s);
})();
