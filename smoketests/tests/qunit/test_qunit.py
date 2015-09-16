# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.qunit import QunitPage


class TestQunit(object):
    @pytest.mark.nondestructive
    def test_qunit(self, mozwebqa):
        qunit_pg = QunitPage(mozwebqa)
        qunit_pg.go_to_qunit_page()
        qunit_pg.wait_for_completion()
        assert qunit_pg.check_all_passed()
