test("basic email validation", function() {
    var i;
    var test_data = [
        ['', false],
        ['abc', false],
        ['foo@', false],
        ['foo@example.com', true],
        ['foo.bar@baz.example.com', true]
    ];

    for (i=0; i < test_data.length; i++) {
        var item = test_data[i];
        ok(fjord.validateEmail(item[0]) == item[1], item);
    }
});
