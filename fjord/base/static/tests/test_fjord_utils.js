test("basic email validation", function() {
    var i;
    var test_data = [
        ['', false],
        ['abc', false],
        ['foo@', false],
        ['foo@example.com', true],
        ['foo.bar@baz.example.com', true],
        ['foo+bar@baz.example.com', true]
    ];

    for (i=0; i < test_data.length; i++) {
        var item = test_data[i];
        ok(fjord.validateEmail(item[0]) == item[1], item);
    }
});

test("basic url validation", function() {
    var i;
    var test_data = [
        ['a', false],
        ['about:start', false],
        ['chrome://somepage', false],
        ['http://example', false],
        ['', true],
        ['example.com', true],
        ['ftp://example.com', true],
        ['http://example.com', true],
        ['https://example.com', true],
        ['https://foo.example.com:8000/blah/blah/?foo=bar#baz', true],
        ['http://mozilla.org/\u2713', true]
    ];

    for (i=0; i < test_data.length; i++) {
        var item = test_data[i];
        ok(fjord.validateUrl(item[0]) == item[1], item);
    }
});
// FIXME: This causes qunit to reload the page which causes problems.
// It'd be nice if we could test this without causing problems.
// test("set and get querystring", function() {
//     var data = {
//         'foo': 'bar'
//     };

//     fjord.setQuerystring(data);
//     var qs = fjord.getQuerystring();

//     ok(qs.foo == 'bar');
// });
