#!/usr/bin/env python

import sys
import re

import requests
from requests.exceptions import (
    ConnectionError,
    Timeout
    )

BUG_PREFIX_REGEX = r'\[bug (\d+)\]'


def are_lines_not_more_than_79_chars(contents):
    if filter(lambda x: len(x) > 79, contents):
        print('Error:')
        print('The commit message should not have more than '
              '79 characters per line')
        return False
    return True


def is_bug_number_in_right_format(contents):
    summary = contents[0]
    if (re.compile(r'\bbug\b', flags=re.IGNORECASE).search(summary) and
            re.search(r'\b#{0,1}\d+\b', summary)):
        bug_format_regex = re.compile(BUG_PREFIX_REGEX,
                                      flags=re.IGNORECASE)
        valid_bug_format = bug_format_regex.match(summary)
        if not valid_bug_format:
            print('Specify the bug number in the format '
                  '[bug xxxxxxx] at the beginning of the commit summary')
            return False
    return True


def print_bug_info(contents):
    summary = contents[0]
    bug_id_regex = re.compile(BUG_PREFIX_REGEX,
                              flags=re.IGNORECASE)
    is_a_bug = bug_id_regex.match(summary)
    if is_a_bug:
        bug_id = is_a_bug.group(1)
        url = 'https://bugzilla.mozilla.org/rest/bug/{}'.format(bug_id)
        try:
            response = requests.get(url, timeout=60.0)
            response_dict = response.json()
            if ('error' in response_dict and response_dict['error']):
                print('Bug with id {} not found.'.format(bug_id))
                return False
            bug_info = response_dict['bugs'][0]
            print('{} - {}'.format(bug_id,
                                   bug_info['summary']))
            print('Assigned to: {}'.format(bug_info['assigned_to']))
        except ValueError:
            print('Error parsing response from Bugzilla REST API')
        except (ConnectionError, Timeout):
            print('Unable to contact Mozilla Bugzilla')
    return True

LINT_FUNCTIONS = [is_bug_number_in_right_format,
                  are_lines_not_more_than_79_chars,
                  print_bug_info]


def lint_commit_msg(commit_msg_file):
    with open(commit_msg_file) as commit_contents:
        commit_msg = commit_contents.readlines()
        return_values = map(lambda x: x(commit_msg), LINT_FUNCTIONS)
        if not all(return_values):
            return 1
    return 0

if __name__ == '__main__':
    commit_msg_file = sys.argv[1]
    errors_found = lint_commit_msg(commit_msg_file)
    if errors_found:
        sys.exit(1)
