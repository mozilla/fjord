#!/usr/bin/env python
import datetime
import json
import subprocess
import sys
import urllib

import requests


BUGZILLA_API_URL = 'https://api-dev.bugzilla.mozilla.org/latest'

QUARTERS = {
    1: [(1, 1), (3, 31)],
    2: [(4, 1), (6, 30)],
    3: [(7, 1), (9, 30)],
    4: [(10, 1), (12, 31)]
}

USAGE = 'Usage: quarter_in_review.py <year> <quarter>'
HEADER = 'quarter_in_review.py: find out what happened!'


all_people = set()


def bugzilla_me_now(params):
    url = BUGZILLA_API_URL + '/bug'

    r = requests.request(
        'GET',
        url,
        params=params,
        timeout=60.0
    )
    if r.status_code != 200:
        raise Exception(r.text)

    return json.loads(r.text)


def print_bugzilla_stats(from_date, to_date):
    # FIXME:
    # created: bugs where creation_time is between the two dates
    # fixed: bugs where fixed between the two dates
    params = {
        'product': 'Input',
        'f1': 'creation_ts',
        'o1': 'greaterthaneq',
        'v1': from_date.strftime('%Y-%m-%d'),
        'f2': 'creation_ts',
        'o2': 'lessthan',
        'v2': to_date.strftime('%Y-%m-%d')
    }

    resp = requests.get('https://bugzilla.mozilla.org/rest/bug?' +
                        urllib.urlencode(params))
    json_data = resp.json()
    if 'error' in json_data and json_data['error']:
        print 'ERROR', json_data

    creation_count = len(json_data['bugs'])

    creators = {}
    for bug in json_data['bugs']:
        creator = bug['creator_detail']['real_name']
        creators[creator] = creators.get(creator, 0) + 1

    params = {
        'product': 'Input',
        'f1': 'cf_last_resolved',
        'o1': 'greaterthaneq',
        'v1': from_date.strftime('%Y-%m-%d'),
        'f2': 'cf_last_resolved',
        'o2': 'lessthan',
        'v2': to_date.strftime('%Y-%m-%d')
    }

    resp = requests.get('https://bugzilla.mozilla.org/rest/bug?' +
                        urllib.urlencode(params))
    json_data = resp.json()
    if 'error' in json_data and json_data['error']:
        print 'ERROR', json_data

    resolved_count = len(json_data['bugs'])

    resolved_map = {}
    resolvers = {}
    for bug in json_data['bugs']:
        resolution = bug['resolution']
        resolved_map[resolution] = resolved_map.get(resolution, 0) + 1
        assigned = bug['assigned_to_detail']['real_name']
        resolvers[assigned] = resolvers.get(assigned, 0) + 1

    print 'Bugs created: %s' % creation_count
    print 'Creators:'
    print ''
    creators = sorted(creators.items(), reverse=True, key=lambda item: item[1])
    for person, count in creators:
        print ' %40s : %s' % (person, count)
    print ''

    print 'Bugs resolved: %s' % resolved_count
    print ''
    for resolution, count in resolved_map.items():
        print ' %40s : %s' % (resolution, count)
    print ''
    print 'Resolvers:'
    print ''
    resolvers = sorted(resolvers.items(), reverse=True,
                       key=lambda item: item[1])
    for person, count in resolvers:
        print ' %40s : %s' % (person, count)


def git(*args):
    return subprocess.check_output(args)


def print_git_stats(from_date, to_date):
    all_commits = subprocess.check_output([
        'git', 'log',
        '--after=' + from_date.strftime('%Y-%m-%d'),
        '--before=' + to_date.strftime('%Y-%m-%d'),
        '--format=%H'
    ])

    all_commits = all_commits.splitlines()

    # Person -> # commits
    committers = {}

    # Person -> (# files changed, # inserted, # deleted)
    changes = {}

    for commit in all_commits:
        author = git('git', 'log', '--format=%an',
                     '{0}~..{1}'.format(commit, commit))

        author = author.strip()
        # FIXME - this is lame. what's going on is that there are
        # merge commits which have multiple authors, so we just grab
        # the second one.
        if '\n' in author:
            author = author.splitlines()[1]

        committers[author] = committers.get(author, 0) + 1

        diff_data = git('git', 'diff', '--numstat', '--find-copies-harder',
                        '{0}~..{1}'.format(commit, commit))
        total_added = 0
        total_deleted = 0
        total_files = 0

        for line in diff_data.splitlines():
            added, deleted, fn = line.split('\t')
            if fn.startswith('vendor/'):
                continue
            if added != '-':
                total_added += int(added)
            if deleted != '-':
                total_deleted += int(deleted)
            total_files += 1

        old_changes = changes.get(author, (0, 0, 0))
        changes[author] = (
            old_changes[0] + total_added,
            old_changes[1] + total_deleted,
            old_changes[2] + total_files
        )

    print 'Total commits:', len(all_commits)
    print ''

    committers = sorted(
        committers.items(), key=lambda item: item[1], reverse=True)
    for person, count in committers:
        print '  %20s : %s  (+%s, -%s, files %s)' % (
            person, count,
            changes[person][0], changes[person][1], changes[person][2])
        all_people.add(person)

    # This is goofy summing, but whatevs.
    print ''
    print 'Total lines added:', sum([item[0] for item in changes.values()])
    print 'Total lines deleted:', sum([item[1] for item in changes.values()])
    print 'Total files changed:', sum([item[2] for item in changes.values()])


def print_header(text):
    print ''
    print text
    print '=' * len(text)
    print ''


def main(argv):
    # XXX: This helps debug bugzilla xmlrpc bits.
    # logging.basicConfig(level=logging.DEBUG)

    if len(argv) < 2:
        print USAGE
        print 'Error: Must specify year and quarter. Example:'
        print 'quarter_in_review.py 2014 1'
        return 1

    # FIXME: add argument validation here
    year, quarter = argv
    year = int(year)
    quarter = int(quarter)
    quarter_dates = QUARTERS[quarter]

    from_date = datetime.date(year, quarter_dates[0][0], quarter_dates[0][1])
    to_date = datetime.date(year, quarter_dates[1][0], quarter_dates[1][1])

    print HEADER

    print_header('Quarter %sq%s (%s -> %s)' % (
        year, quarter, from_date, to_date))

    print_header('Bugzilla')
    print_bugzilla_stats(from_date, to_date)

    print_header('git')
    print_git_stats(from_date, to_date)

    # print all_people


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
