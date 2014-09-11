$(function() {
    var $vhistogram = $('.graph .versionhistogram');

    // Datepickers.
    if (!fjord.isDateInputSupported()) {
        $('input[type=date]').datepicker({
            dateFormat: 'yy-mm-dd'
        });
    }

    // Set up the when selector.
    var $date_start = $('#whensubmit').siblings('input[name=date_start]');
    var $date_end = $('#whensubmit').siblings('input[name=date_end]');
    $('#whensubmit').bind('click', function() {
        fjord.setQuerystring(fjord.getQuerystring(), {
            date_start: $date_start.val(),
            date_end: $date_end.val()
        });
    });

    function weekends(axes) {
        var markings = [];

        // Start with the minimum xaxis tick
        var d = new Date(axes.xaxis.min);

        // Move to the first weekend day
        d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 1) % 7));
        d.setUTCSeconds(0);
        d.setUTCMinutes(0);
        d.setUTCHours(0);

        var stamp = d.getTime();
        var day = 24 * 60 * 60 * 1000;

        // Iterate to the maximum xaxis figuring out each weekend
        // block and adding a thing to the xaxis markings.
        while (stamp < axes.xaxis.max) {
            markings.push({
                xaxis: {
                    from: stamp,
                    to: stamp + (2 * day)
                }
            });
            stamp += 7 * day;
        }

        return markings;
    }

    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 12,
            border: '1px solid #bbb',
            padding: '4px',
            'background-color': '#eeeeee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    function drawTotals() {
        var $histogram = $('.graph .histogram');
        var data = $histogram.data('histogram');
        var options = {
            series: {
                hover: true
            },
            grid: {
                hoverable: true,
                markings: weekends
            },
            xaxis: {
                mode: 'time',
                timeformat: ('%b %d')
            },
            yaxes: [
                {
                    min: 0,
                    position: 'left'
                },
                {
                    max: 30,
                    min: -30,
                    position: 'right'
                }
            ],
            legend: {
                container: $('#totalslegend'),
                noColumns: 3
            }
        };

        var plot = $.plot($histogram, data, options);

        var previousPoint = null;
        $histogram.bind("plothover", function(event, pos, item) {
            if (item) {
                if (previousPoint != item.dataIndex) {
                    previousPoint = item.dataIndex;

                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(0);
                    var y = item.datapoint[1].toFixed(0);
                    var xDate = new Date(Math.floor(x));
                    var text = (xDate.getFullYear() + '-'
                                + (xDate.getMonth() + 1) + '-'
                                + (xDate.getDate() + 1));

                    showTooltip(item.pageX, item.pageY, text + ' = ' + y);
                }
            } else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        });
    }

    function drawVersions() {
        var $histogram = $('.graph .versionshistogram');
        var data = $histogram.data('histogram');
        var options = {
            series: {
                hover: true
            },
            grid: {
                hoverable: true,
                markings: weekends
            },
            xaxis: {
                mode: 'time',
                timeformat: ('%b %d')
            },
            yaxis: {
                min: 0,
                position: 'left'
            },
            legend: {
                sorted: true,
                container: $('#versionslegend'),
                noColumns: 4
            }
        };

        var plot = $.plot($histogram, data, options);

        var previousPoint = null;
        $histogram.bind("plothover", function(event, pos, item) {
            if (item) {
                if (previousPoint != item.dataIndex) {
                    previousPoint = item.dataIndex;

                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(0);
                    var y = item.datapoint[1].toFixed(0);
                    var xDate = new Date(Math.floor(x));
                    var text = (xDate.getFullYear() + '-'
                                + (xDate.getMonth() + 1) + '-'
                                + (xDate.getDate() + 1));

                    showTooltip(item.pageX, item.pageY, text + ' = ' + y);
                }
            } else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        });
    }

    function drawPlatforms() {
        var $histogram = $('.graph .platformshistogram');
        var data = $histogram.data('histogram');
        var options = {
            series: {
                hover: true
            },
            grid: {
                hoverable: true,
                markings: weekends
            },
            xaxis: {
                mode: 'time',
                timeformat: ('%b %d')
            },
            yaxis: {
                min: 0,
                position: 'left'
            },
            legend: {
                sorted: true,
                container: $('#platformslegend'),
                noColumns: 4
            }
        };

        var plot = $.plot($histogram, data, options);

        var previousPoint = null;
        $histogram.bind("plothover", function(event, pos, item) {
            if (item) {
                if (previousPoint != item.dataIndex) {
                    previousPoint = item.dataIndex;

                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(0);
                    var y = item.datapoint[1].toFixed(0);
                    var xDate = new Date(Math.floor(x));
                    var text = (xDate.getFullYear() + '-'
                                + (xDate.getMonth() + 1) + '-'
                                + (xDate.getDate() + 1));

                    showTooltip(item.pageX, item.pageY, text + ' = ' + y);
                }
            } else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        });
    }

    drawTotals();
    drawVersions();
    drawPlatforms();
});
