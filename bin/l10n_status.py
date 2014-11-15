#!/usr/bin/env python

import argparse
import requests
import sys
import time

try:
    import blessings
    TERM = blessings.Terminal()
except ImportError:
    class Terminal(object):
        def __getattr__(self, k):
            return lambda x: x

    TERM = Terminal()


USAGE = 'usage: l10n_status.py [OPTIONS] url'
DESC = 'Displays translation progress data'


def is_good(day):
    try:
        day['locales']['fr']['apps']
        return True
    except KeyError:
        return False


def get_data(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        resp.raise_for_status()

    data = resp.json()

    # Nix "bad data" that I've got in my environments because I've
    # been tweaking the format over time.
    # FIXME - change this to support previous formats and convert
    # forward.
    data = [day for day in data if is_good(day)]

    return data


def format_time(t):
    return time.ctime(t)


def format_short_date(t):
    return time.strftime('%m/%d', time.gmtime(t))


def format_bar(p):
    return '=' * (p / 2) + ' ' + str(p)


def display_summary(last_item, app, highlight):
    # Show summary
    if app:
        print 'Showing app: {0}'.format(app)

    data = last_item['locales']

    if app:
        get_data = lambda x: x['apps'][app]['percent']
    else:
        get_data = lambda x: x['percent']

    items = [item for item in data.items() if item[0] not in highlight]
    hitems = [item for item in data.items() if item[0] in highlight]

    if hitems:
        print 'Highlighted locales:'

        for loc, loc_data in sorted(hitems, key=lambda x: -x[1]['percent']):
            perc = get_data(loc_data)
            print '{0:>8}: {1}'.format(loc, format_bar(perc))
        print ''

    print 'Locales:'
    for loc, loc_data in sorted(items, key=lambda x: -x[1]['percent']):
        perc = get_data(loc_data)
        print '{0:>8}: {1}'.format(loc, format_bar(perc))


def mark_movement(data, space):
    """Adds ^ and v for up and down movement based on previous day"""
    ret = []
    for i, day in enumerate(data):
        item = data[i]

        if i == 0:
            ret.append(item)
            continue

        prespace = ' ' * (space - len(str(item)) - 1)
        if data[i-1] > item:
            item = prespace + TERM.bold_red('v' + str(item))
        elif data[i-1] < item:
            item = prespace + TERM.bold_green('^' + str(item))
        elif item < 100:
            item = prespace + TERM.bold_yellow('=' + str(item))

        ret.append(item)

    return ret


def display_history(data, app, highlight):
    # Get a list of the locales we'll iterate through
    locales = sorted(data[-1]['locales'].keys())

    num_days = 14

    # Truncate the data to what we want to look at
    # FIXME - adjust this to show more depending on console width
    data = data[-num_days:]

    # Build the template: locale, completed per day, tags
    tmpl = '{:>8} ' + ('{:>6}' * len(data)) + '  {:10}'

    # Get a list of dates -- show last 2 weeks
    dates = [item['created'] for item in data]

    # Print the header
    values = [''] + [format_short_date(day) for day in dates] + ['']
    print tmpl.format(*values)

    if app:
        get_data = lambda x: x['apps'][app]['percent']
    else:
        get_data = lambda x: x['percent']

    hlocales = [loc for loc in locales if loc in highlight]
    locales = [loc for loc in locales if loc not in highlight]

    def print_data(loc_list, data):
        for loc in loc_list:
            values = []
            values.append(loc)
            day_data = [get_data(day['locales'][loc]) for day in data]
            values.extend(mark_movement(day_data, 6))

            if day_data[-1] < 90:
                values.append('**')
            else:
                values.append('')

            print tmpl.format(*values)

    if hlocales:
        print 'Highlighted locales:'
        print_data(hlocales, data)
        print ''

    if locales:
        print 'Locales:'
        print_data(locales, data)


def main(argv):
    parser = argparse.ArgumentParser(
        description=DESC, usage=USAGE,
        epilog='Note: Install blessings for color.')
    parser.add_argument('--app',
                        help='Specify the app to show data for')
    parser.add_argument('--highlight', default=[],
                        help='Comma separated list of important locales')
    parser.add_argument('--type', default='summary',
                        choices=['summary', 'history'],
                        help='Report to view')
    parser.add_argument('url', help='URL for your data')

    args = parser.parse_args()

    data = get_data(args.url)

    if not data:
        print 'No data'
        return 0

    last_item = data[-1]
    print 'URL:     {0}'.format(args.url)
    print 'Created: {0}'.format(format_time(last_item['created']))
    print ''

    if args.type == 'summary':
        display_summary(data[-1], args.app, args.highlight)
    elif args.type == 'history':
        display_history(data, args.app, args.highlight)
    else:
        print 'Unknown display type.'

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
