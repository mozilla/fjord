class TranslationException(Exception):
    """Base class for all translation exceptions"""


class NoSuchSystem(TranslationException):
    """Indicates the specified system doesn't exist"""
