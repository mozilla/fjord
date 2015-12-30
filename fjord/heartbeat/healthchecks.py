from collections import namedtuple
from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import connection
from django.template.loader import render_to_string

from fjord.heartbeat.models import Answer
from fjord.mailinglist.utils import get_recipients


log = logging.getLogger('i.heartbeat')


SEVERITY_LOW = 1
SEVERITY_MEDIUM = 5
SEVERITY_HIGH = 10

SEVERITY = {
    SEVERITY_LOW: 'low',
    SEVERITY_MEDIUM: 'medium',
    SEVERITY_HIGH: 'high'
}


Result = namedtuple('Result', ['name', 'severity', 'summary', 'output'])


CHECKS = []


def register_check(cls):
    CHECKS.append(cls)
    return cls


class Check(object):
    name = ''

    @classmethod
    def check(cls):
        pass


@register_check
class CheckAnyAnswers(Check):
    """Are there any heartbeat answers? If not, that's very bad."""
    name = 'Are there any heartbeat answers?'

    @classmethod
    def check(cls):
        day_ago = datetime.now() - timedelta(days=1)
        count = Answer.objects.filter(received_ts__gt=day_ago).count()

        if count == 0:
            return Result(
                cls.name,
                SEVERITY_HIGH,
                '0 answers in last 24 hours.',
                str(count)
            )
        return Result(
            cls.name,
            SEVERITY_LOW,
            '%s answers in last 24 hours.' % str(count),
            str(count)
        )


def tableify(table):
    """Takes a list of lists and converts it into a formatted table

    :arg table: list (rows) of lists (columns)

    :returns: string

    .. Note::

       This is text formatting--not html formatting.

    """
    num_cols = 0
    maxes = []

    for row in table:
        num_cols = max(num_cols, len(row))
        if len(maxes) < len(row):
            maxes.extend([0] * (len(row) - len(maxes)))
        for i, cell in enumerate(row):
            maxes[i] = max(maxes[i], len(str(cell)))

    def fix_row(maxes, row):
        return '  '.join([
            str(cell) + (' ' * (maxes[i] - len(str(cell))))
            for i, cell in enumerate(row)
        ])

    return '\n'.join(
        [
            fix_row(maxes, row)
            for row in table
        ]
    )


@register_check
class CheckMissingVotes(Check):
    """FIXME: I don't understand this check"""
    name = 'Are there votes of 0 for large cells?'

    @classmethod
    def check(cls):
        # Note: This SQL statement comes from Gregg. It's probably
        # mysql-specific.
        sql = """
        SELECT
            sum(score is not NULL) as nvoted,
            DATE_FORMAT(received_ts, '%Y-%m-%d') as ydm,
            version,
            channel,
            100*sum(flow_began_ts > 0) / count(received_ts) as pct_began,
            100*sum(flow_offered_ts >0) / count(received_ts) as pct_offered,
            100*sum(flow_voted_ts > 0)/ count(received_ts) as pct_voted,
            100*sum(flow_engaged_ts > 0) / count(received_ts) as pct_engaged,
            count(received_ts) as N
        FROM heartbeat_answer
        WHERE
            received_ts > DATE_SUB(now(), interval 1 day)
            AND is_test=0
            AND survey_id="heartbeat-by-user-first-impression"
            AND (locale='en-us')
        GROUP BY version, channel, ydm
        HAVING
            N >= 50
            and nvoted = 0
        ORDER BY
            channel,
            version,
            ydm;
        """
        cursor = connection.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()

        if not data:
            # If we get nothing back, then we have serious issues.
            return Result(
                cls.name,
                SEVERITY_HIGH,
                'No data from query',
                repr(data)
            )

        data = list(data)

        # FIXME: What consistutes SEVERITY_HIGH here?

        data.insert(
            0,
            ['nvoted', 'ydm', 'version', 'channel', 'pct_began', 'pct_offered',
             'pct_voted', 'pct_engaged', 'N']
        )
        return Result(
            cls.name,
            SEVERITY_LOW,
            'Data looks ok.',
            tableify(data)
        )


def get_all_healthchecks():
    return CHECKS


def run_healthchecks():
    return [checker.check() for checker in get_all_healthchecks()]


def email_healthchecks(results):
    has_high = any([result.severity == SEVERITY_HIGH for result in results])

    # The subject should indicate very very obviously whether the sky is
    # falling or not.
    subject = '[hb health] %s (%s)' % (
        ('RED ALERT' if has_high else 'fine'),
        datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    # We do the entire email body in HTML because some output will want to
    # preserve whitespace and use a fixed-width font. Further, this lets
    # us make it super easy to spot SEVERITY_HIGH situations.
    html_body = render_to_string('heartbeat/email/heartbeat_health.html', {
        'severity_name': SEVERITY,
        'results': results
    })

    recipients = get_recipients('heartbeat_health')

    if recipients:
        send_mail(
            subject=subject,
            message='This email is in HTML.',
            from_email=settings.SERVER_EMAIL,
            recipient_list=recipients,
            html_message=html_body
        )

    else:
        # FIXME: log this? is that a good idea?
        log.info('No recipients for "heartbeat_health"' + '\n' +
                 subject + '\n' +
                 html_body)
