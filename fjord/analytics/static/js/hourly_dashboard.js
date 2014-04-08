$(function() {
    var $histogram = $('.graph .hourly-histogram');

    // Datepickers.
    $('input[type=date]').datepicker({
        dateFormat: 'yy-mm-dd',
    });

    // Set up the when selector.
    var $date_end = $('#whensubmit').siblings('input[name=date_end]');
    $('#whensubmit').bind('click', function() {
        setQuerystring(getQuerystring(), {
            date_end: $date_end.val()
        });
    });

    // Draw histogram in the middle column.
    var data = $histogram.data('histogram');
    colors = {
        'hourly': '#723EBF'
    };

    for (var i = 0; i < data.length; i++) {
        var name = data[i]['name'];
        var color = colors[name];
        if (color === undefined) {
            color = '#000000';
        }
        data[i]['color'] = color;
    }
    var options = {
        series: {
            hover: true,
            lines: { show: true, fill: false },
            points: { show: true }
        },
        grid: {
            hoverable: true
        },
        xaxis: {
            mode: 'time',
            timeformat: ('%b %d %H:%M')
        },
        yaxis: {
            min: 0,
            max: 1250
        },
        legend: {
            container: $('.graph .legend'),
            noColumns: 1 // number of columns
        }
    };
    var plot = $.plot($histogram, data, options);

    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 12,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#eef',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
    $histogram.bind("plothover", function (event, pos, item) {
        if (item) {
            if (previousPoint != item.dataIndex) {
                previousPoint = item.dataIndex;

                $("#tooltip").remove();
                var x = item.datapoint[0].toFixed(2);
                var y = item.datapoint[1].toFixed(2);
                var text = new Date(Math.floor(x)).toUTCString();

                // FIXME: So, the data is actuall Pacific time and
                // not UTC. Doing toUTCString() tacks on a "GMT"
                // to the end.  We remove that here in order to
                // put a band-aid on the band-aid.
                text = text.substring(0, text.length - 4);

                showTooltip(item.pageX, item.pageY, text + ' = ' + y);
            }
        } else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    });
});
