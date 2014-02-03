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
        day['locales']['fr']['apps']['feedback']
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


def display_percent(p):
    return '=' * (p / 2) + ' ' + str(p)


def value_or_default(argv, index, default=None):
    try:
        return argv[index]
    except IndexError:
        return default


def display_summary(last_item, app):
    # Show summary
    if app:
        print 'Showing app: {0}'.format(app)

    for loc, loc_data in sorted(last_item['locales'].items(), key=lambda x: -x[1]['percent']):
        if app:
            perc = loc_data['apps'][app]['percent']
        else:
            perc = loc_data['percent']

        print '{0:>8}: {1}'.format(loc, display_percent(perc))


def display_history(data, app, highlight):
    # Get a list of the locales we'll iterate through
    locales = sorted(data[-1]['locales'].keys())

    num_days = 14

    # Truncate the data to what we want to look at
    # FIXME - adjust this to show more depending on console width
    data = data[-num_days:]

    # Build the template
    tmpl = '{:4} {:>6} ' + ('{:>6}' * len(data))
    tmpl += '  {:10}'  # tags

    # Get a list of dates -- show last 2 weeks
    dates = [item['created'] for item in data]

    # Print the header
    values = ['', ''] + [format_short_date(day) for day in dates] + ['']
    print tmpl.format(*values)

    if app:
        get_data = lambda x: x['apps'][app]['percent']
    else:
        get_data = lambda x: x['percent']

    for loc in locales:
        values = []
        if loc in highlight:
            values.append('***')
        else:
            values.append('')

        values.append(loc)
        values.extend([get_data(day['locales'][loc]) for day in data])

        if values[-1] < 90:
            values.append('Ugh.')
        else:
            values.append('')

        if loc in highlight:
            print TERM.bold_green(tmpl.format(*values))
        else:
            print tmpl.format(*values)


def main(argv):
    parser = argparse.ArgumentParser(description=DESC, usage=USAGE)
    parser.add_argument('--app', help='Specify the app to show data for')
    parser.add_argument('--highlight', default=[], help='Comma separated list of important locales')
    parser.add_argument('--type', default='summary', choices=['summary', 'history'])
    parser.add_argument('url', help='URL for your data')

    args = parser.parse_args()

    data = get_data(args.url)

    if not data:
        print 'No data'
        return 0

    last_item = data[-1]
    print 'Created: {0}'.format(format_time(last_item['created']))

    if args.type == 'summary':
        display_summary(data[-1], args.app)
    elif args.type == 'history':
        display_history(data, args.app, args.highlight)
    else:
        print 'Unknown display type.'

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
