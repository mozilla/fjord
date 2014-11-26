  function getQueryParams () {
    return getParams(window.location.search.substr(1));
  }

  function getParams (qstring) {
    var queryParams = {};
    var stringPair, pair;
    if(qstring.length > 1) {
      stringPair = qstring.split('&');
      for(var i = 0; i < stringPair.length ; i++) {
        pair = stringPair[i].split('=');
        queryParams[pair[0]] = pair[1];
      }
    }
    return queryParams;
  }

  function setupGA () {
    function doSomething (gaAction, url) {
      return function (e) {
        console.log(url);
        console.log(gaAction);
        var qargs = getQueryParams();
        console.log(qargs);
        var label = [qargs.armname, qargs.score].join('::');
        console.log(label);
        // ga('send', 'event', 'heartbeat-telemetry-experiment-1', gaAction, label);
        _gaq.push([
          '_trackEvent',
          'heartbeat-telemetry-experiment-1',
          gaAction,
          label
          ]);
      }
    }
    var ga_links = document.querySelectorAll('.ga-link');

    for (var i = 0; i < ga_links.length; i++) {
      var url = ga_links[i].href;
      ga_links[i].onclick = doSomething(ga_links[i].dataset.gaAction, url);
    };
  }

  // console.log(getQueryParams());
  setupGA();