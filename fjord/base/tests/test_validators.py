from django.core.exceptions import ValidationError

import pytest

from fjord.base.validators import EnhancedURLValidator


class TestEnhancedURLValidator:
    def test_valid_urls(self):
        test_data = [
            'example.com',
            'example.com:80',
            'example.com:80/foo',
            'http://example.com',
            'http://example.com/foo',
            'http://example.com:80',
            'http://example.com:80/foo',
            'https://example.com',
            'https://example.com/foo',
            'https://example.com:80',
            'https://example.com:80/foo',
            'ftp://example.com',
            'about:mozilla',
            'chrome://foo',

            # Taken from Django's URLValidator test case data
            'http://www.djangoproject.com/',
            'http://localhost/',
            'http://example.com/',
            'http://www.example.com/',
            'http://www.example.com:8000/test'
            'http://valid-with-hyphens.com/',
            'http://subdomain.example.com/',
            'http://200.8.9.10/',
            'http://200.8.9.10:8000/test',
            'http://valid-----hyphens.com/',
            'http://example.com?something=value',
            'http://example.com/index.php?something=value&another=value2',
        ]

        validator = EnhancedURLValidator()

        for url in test_data:
            validator(url)

    def test_invalid_urls(self):
        test_data = [
            'foo',
            'http://',
            'http://example',
            'http://example.'
            'http://.com',
            'http://invalid-.com',
            'http://-invalid.com',
            'http://inv-.alid-.com',
            'http://inv-.-alid.com'
        ]

        validator = EnhancedURLValidator()

        for url in test_data:
            with pytest.raises(ValidationError):
                validator(url)
