import logging
import logging.handlers
import socket

from django.conf import settings
from django.utils.log import dictConfig

import commonware.log


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


base_fmt = ('%(name)s:%(levelname)s %(message)s '
            ':%(pathname)s:%(lineno)s')
use_syslog = settings.HAS_SYSLOG and not settings.DEBUG

if use_syslog:
    hostname = socket.gethostname()
else:
    hostname = 'localhost'

cfg = {
    'version': 1,
    'filters': {},
    'formatters': {
        'debug': {
            '()': commonware.log.Formatter,
            'datefmt': '%H:%M:%s',
            'format': '%(asctime)s ' + base_fmt,
        },
        'prod': {
            '()': commonware.log.Formatter,
            'datefmt': '%H:%M:%s',
            'format': '%s %s: [%%(REMOTE_ADDR)s] %s' % (hostname,
                                                        settings.SYSLOG_TAG,
                                                        base_fmt),
        },
    },
    'handlers': {
        'console': {
            '()': logging.StreamHandler,
            'formatter': 'debug',
        },
        'syslog': {
            '()': logging.handlers.SysLogHandler,
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL7,
            'formatter': 'prod',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'null': {
            '()': NullHandler,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {},
}

for key, value in settings.LOGGING.items():
    cfg[key].update(value)

# Set the level and handlers for all loggers.
for logger in cfg['loggers'].values() + [cfg['root']]:
    if 'handlers' not in logger:
        logger['handlers'] = ['syslog' if use_syslog else 'console']
    if 'level' not in logger:
        logger['level'] = settings.LOG_LEVEL
    if logger is not cfg['root'] and 'propagate' not in logger:
        logger['propagate'] = False

dictConfig(cfg)


def noop():
    # FIXME: This is here just to reduce pyflakes issues when this is
    # imported for the side-effects. It's gross stacked on gross.
    pass
