$(function() {
    var $histogram = $('.graph .histogram');

    // General widgets.
    // Expandos
    $('.expando').hide();
    $('.expander').bind('click', function() {
        var $this = $(this);
        var $for = $('#' + $this.attr('for'));
        $for.fadeToggle();
        $this.toggleClass('selected');
    });

    // Datepickers.
    $('input[type=date]').datepicker({
        dateFormat: 'yy-mm-dd',
    });


    // Set up the when selector.
    var $date_start = $('#whensubmit').siblings('input[name=date_start]');
    var $date_end = $('#whensubmit').siblings('input[name=date_end]');
    if ($date_start.val() || $date_end.val()) {
        $('#whentext').show();
        $('.expander[for=whentext]').addClass('selected');
    }

    $('#whensubmit').bind('click', function() {
        setQuerystring(getQuerystring(), {
            date_start: $date_start.val(),
            date_end: $date_end.val()
        });
    });


    // Draw bars in the left column.
    $('ul.bars').each(function() {
        var $ul = $(this);
        var total = $ul.data('total');
        var max_value = 0;
        var $all_li = $ul.children('li');
        var width = $ul.width();
        var name = $ul.attr('name');

        // Find the maximum value, which will have width=100%
        $all_li.each(function() {
            var $li = $(this);
            var value = $li.data('value');
            if (value > max_value) {
                max_value = value;
            }
        });

        $all_li.each(function() {
            var $li = $(this);
            var value = $li.data('value');
            var bar_width = (value / max_value * 100).toString() + '%';
            var percent = (value / total * 100).toFixed(0).toString() + '%';
            var $label = $li.children('label');

            // Draw bars
            $('<span class="bar_bg"/>').css({'width': bar_width}).prependTo($label);
            $('<span class="percent"/>').text(percent).appendTo($label);
            $('<span class="count"/>').text(value).appendTo($label);

            // Click events for faceting
            $li.children('input').bind('click', function() {
                var $input = $(this);
                var params = {};
                if ($input.attr('checked')) {
                    params[name] = $(this).attr('value');
                } else {
                    params[name] = undefined;
                }
                setQuerystring(getQuerystring(), params);
            });
        });
    });

    if ($histogram.length !== 0) {

        // Draw histogram in the middle column.
        var data = $histogram.data('histogram');
        colors = {
            'happy': '#72BF3E',
            'sad': '#AA4643'
        };
        for (var i = 0; i < data.length; i++) {
            var name = data[i]['name'];
            var color = colors[name];
            if (color === undefined) {
                color = '#000000';
            }
            data[i]['color'] = color;
        }

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

        var options = {
            series: {
                hover: true,
                lines: { show: true, fill: false },
                points: { show: true }
            },
            grid: {
                markings: weekends
            },
            xaxis: {
                mode: 'time',
                timeformat: ('%b %d')
            },
            yaxis: {
                min: 0
            },
            legend: {
                container: $('.graph .legend'),
                noColumns: 2
            }
        };
        var plot = $.plot($histogram, data, options);
    }
});
