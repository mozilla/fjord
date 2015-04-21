#!/usr/bin/env python

import os
import re
import subprocess
import sys
import textwrap

import requests
from requests.exceptions import (
    ConnectionError,
    Timeout
)

BUG_PREFIX_REGEX = r'\[bug (\d+)\]'


def wrap_paragraphs(text):
    paragraphs = [
        '\n'.join(textwrap.wrap(paragraph))
        for paragraph in text.split('\n')
    ]
    return '\n'.join(paragraphs)


def are_lines_not_more_than_79_chars(contents):
    errors = []
    for lineno, line in enumerate(contents):
        if len(line) > 79:
            errors.append(
                '%s: Line is longer than 79 characters.' % (lineno + 1)
            )

    return errors


def is_bug_number_in_right_format(contents):
    summary = contents[0]
    if (re.compile(r'\bbug\b', flags=re.IGNORECASE).search(summary) and
            re.search(r'\b#{0,1}\d+\b', summary)):
        bug_format_regex = re.compile(BUG_PREFIX_REGEX,
                                      flags=re.IGNORECASE)
        valid_bug_format = bug_format_regex.match(summary)
        if not valid_bug_format:
            return ['1: Bug number is in wrong format. Use [bug xxxxxx].']
    return []


def print_bug_info(contents):
    summary = contents[0]
    bug_id_regex = re.compile(BUG_PREFIX_REGEX,
                              flags=re.IGNORECASE)
    is_a_bug = bug_id_regex.match(summary)
    if is_a_bug:
        bug_id = is_a_bug.group(1)
        url = 'https://bugzilla.mozilla.org/rest/bug/{}'.format(bug_id)
        try:
            print 'Looking up bug {}...'.format(bug_id)
            response = requests.get(url, timeout=60.0)
            response_dict = response.json()
            if ('error' in response_dict and response_dict['error']):
                print('Bug not found!')
                return []
            print 'Found!'
            bug_info = response_dict['bugs'][0]
            print '    Summary: {}'.format(bug_info['summary'])
            print '    Assigned to: {}'.format(bug_info['assigned_to'])
        except ValueError:
            print 'Error parsing response from Bugzilla REST API.'
        except (ConnectionError, Timeout):
            print 'Unable to contact Mozilla Bugzilla.'
    return []


LINT_FUNCTIONS = [
    is_bug_number_in_right_format,
    are_lines_not_more_than_79_chars,
    print_bug_info
]


HEADER = '# COMMIT MESSAGE ERRORS:'


def lint_commit_msg(commit_msg_file, editor):
    while True:
        commit_msg = []

        with open(commit_msg_file) as fp:
            for line in fp:
                # Only strip the right side. That way we don't screw
                # up any indentation from the original message.
                line = line.rstrip()

                # Break out of loop if we hit the error header or the
                # git commit message instructions.
                if line == HEADER or line.startswith('# '):
                    break

                commit_msg.append(line)

        # Lint functions should return lists of strings where each
        # string is an error message. If they have warnings, they
        # should just print the warnings to stdout.
        errors = []
        for func in LINT_FUNCTIONS:
            errors.extend(func(commit_msg))

        if not errors:
            return 0

        print 'Invalid git commit message:'
        print ''
        print '\n'.join(errors)
        print ''
        if not editor:
            print (
                wrap_paragraphs(
                    'You do not have EDITOR set in your environment. Please '
                    'set EDITOR in your environment if you want to edit the '
                    'commit message when there are errors. In the meantime '
                    'you can do:\n'
                    '\n'
                    'git commit --amend\n'
                    '\n'
                    'to fix the issues listed above.'
                )
            )
            return 0

        print (
            'Would you like to edit the message?\n'
            '* y (yes): edit commit with %s\n'
            '* n (no): the commit will fail\n'
            '* i (ignore): the commit will succeed as is'
        ) % editor
        print ''
        ret = raw_input('Edit commit message? [Y/n/i] ')

        ret = ret.strip()
        ret = ret.lower().strip()[:1]
        if not ret or ret == 'n':
            print 'Rejecting commit message...'
            return 1
        if ret == 'i':
            print 'Ignoring errors...'
            return 0

        commit_msg.append(HEADER)
        commit_msg.extend(['# ' + error for error in errors])

        # Rewrite the commit message file with the errors. Then
        # start the editor with it.
        with open(commit_msg_file, 'w') as fp:
            fp.write('\n'.join(commit_msg))

        subprocess.call('%s %s' % (editor, commit_msg_file), shell=True)

        # Go through the loop again.

    return 0


if __name__ == '__main__':
    commit_msg_file = sys.argv[1]
    editor = os.environ.get('EDITOR', '')
    errors_found = lint_commit_msg(commit_msg_file, editor)

    if errors_found:
        sys.exit(1)
