# encoding: utf8
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Sync Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Tarek Ziade (tarek@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
from datetime import datetime
import logging
import os
import syslog
from tempfile import mkstemp
import unittest

from cef import log_cef, logger, _Formatter, SysLogFormatter


class TestCEFLogger(unittest.TestCase):

    def setUp(self):
        self.environ = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_HOST': '127.0.0.1',
                        'PATH_INFO': '/', 'REQUEST_METHOD': 'GET',
                        'HTTP_USER_AGENT': 'MySuperBrowser'}

        self.config = {'cef.version': '0', 'cef.vendor': 'mozilla',
                       'cef.device_version': '3', 'cef.product': 'weave',
                       'cef': True}
        self.filename = self.config['cef.file'] = mkstemp()[1]
        self._warn = []

        def _warning(warn):
            self._warn.append(warn)

        self.old_logger = logger.warning
        logger.warning = _warning

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        logger.warning = self.old_logger
        self._warn[:] = []

    def _log(self, name, severity, *args, **kw):
        log_cef(name, severity, self.environ, self.config, *args, **kw)

        if os.path.exists(self.filename):
            with open(self.filename) as f:
                content = f.read()

            os.remove(self.filename)
        else:
            content = ''

        return content

    def test_cef_logging(self):
        # should not fail
        res = self._log('xx|x', 5)
        self.assertEquals(len(res.split('|')), 10)

        # should not fail and be properly escaped
        self.environ['HTTP_USER_AGENT'] = "=|\\"
        content = self._log('xxx', 5)

        cs = 'cs1Label=requestClientApplication cs1=\=|\\\\ '
        self.assertTrue(cs in content)

        # should log.warn because extra keys shouldn't have pipes
        self._log('xxx', 5, **{'ba|d': 1})
        self.assertEqual('The "ba|d" key contains illegal characters',
                         self._warn[0])

    def test_cef_syslog(self):
        try:
            import syslog   # NOQA
        except ImportError:
            return

        self.config['cef.file'] = 'syslog'
        self.config['cef.syslog.priority'] = 'ERR'
        self.config['cef.syslog.facility'] = 'AUTH'
        self.config['cef.syslog.options'] = 'PID,CONS'

        self._log('xx|x', 5)

        # XXX how to get the facility filename via an API ?
        # See http://bugs.python.org/issue10595
        if not os.path.exists('/var/log/auth.log'):
            return

        with open('/var/log/auth.log') as f:
            logs = '\n'.join(f.read().split('\n')[-10:])

        self.assertTrue('MySuperBrowser' in logs)

    def test_cef_nohost(self):
        try:
            import syslog   # NOQA
        except ImportError:
            return

        self.environ['HTTP_USER_AGENT'] = 'MySuperBrowser2'
        self.config['cef.file'] = 'syslog'
        self.config['cef.syslog.priority'] = 'ERR'
        self.config['cef.syslog.facility'] = 'AUTH'
        self.config['cef.syslog.options'] = 'PID,CONS'

        self._log('xx|x', 5)

        # XXX how to get the facility filename via an API ?
        # See http://bugs.python.org/issue10595
        if not os.path.exists('/var/log/auth.log'):
            return

        with open('/var/log/auth.log') as f:
            logs = '\n'.join(f.read().split('\n')[-10:])

        self.assertTrue('MySuperBrowser2' in logs)

    def test_suser(self):
        content = self._log('xx|x', 5, username='me')
        self.assertTrue('suser=me' in content)

    def test_custom_extensions(self):
        content = self._log('xx|x', 5, username='me',
                            custom1='ok')
        self.assertTrue('custom1=ok' in content)

    def test_too_big(self):
        big = 'i' * 500
        bigger = 'u' * 550
        content = self._log('xx|x', 5, username='me',
                            custom1='ok', big=big, bigger=bigger)
        self.assertTrue('big=ii' in content)
        self.assertFalse('bigger=uu' in content)
        self.assertTrue('CEF Message too big' in self._warn[0])

    def test_conversions(self):
        content = self._log('xx\nx|xx\rx', 5, username='me',
                            ext1='ok=ok', ext2='ok\\ok')
        self.assertTrue('xx\\\nx\\|xx\\\rx' in content)
        self.assertTrue("ext1=ok\\=ok ext2=ok\\\\ok" in content)

    def test_default_signature(self):
        content = self._log('xx', 5)
        self.assertTrue('xx|xx' in content)

    def test_formater_unicode(self):
        config = {'cef.version': '0', 'cef.vendor': 'mozilla',
                  'cef.device_version': '3', 'cef.product': 'weave',
                  'cef': True, 'cef.file': mkstemp()[1]}
        file_ = config['cef.file']

        environ = {'PATH_INFO':
                u'/reviewers/receipt/issue/\u043f\u0442\u0442-news'}
        kw = {'cs2': 1L,
              'cs2Label': u'\xd0'}

        log_cef('name', 0, environ, config, username=u'tarek', **kw)
        with open(file_) as f:
            data = f.read()

        self.assertTrue('cs2Label=\xc3\x90' in data, data)


class TestCEFFormatter(unittest.TestCase):

    def setUp(self):
        self.environ = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_HOST': '127.0.0.1',
                        'PATH_INFO': '/', 'REQUEST_METHOD': 'GET',
                        'HTTP_USER_AGENT': 'MySuperBrowser'}

        class record:
            level = 'foo'
            msg = 'Test message'
            args = {'severity': 1, 'environ': self.environ, 'data': {}}
        self.record = record()

    def test_formatter_no_date(self):
        fmt = _Formatter()
        assert fmt.format(self.record)

    def test_formatter_date(self):
        fmt = _Formatter()
        fmt.datefmt = '%H:%M'
        assert (fmt.format(self.record)
                   .startswith(datetime.today().strftime('%H:%M')))

    def test_formatter_level(self):
        fmt = SysLogFormatter()
        self.record.levelno = logging.DEBUG
        data = fmt.format(self.record)
        assert data.split('|')[6] == str(syslog.LOG_DEBUG)


if __name__ == '__main__':
    unittest.main()
