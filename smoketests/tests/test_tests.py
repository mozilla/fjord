from . import BaseTestCase, nondestructive


class TestTests(BaseTestCase):
    def test_destructive(self):
        pass

    @nondestructive
    def test_non_destructive(self):
        pass
