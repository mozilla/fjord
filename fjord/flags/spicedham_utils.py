import json
import os
import re
import threading

from spicedham import Spicedham
from spicedham.backend import BaseBackend

from fjord.flags.models import Store


class FjordBackend(BaseBackend):
    def __init__(self, config):
        pass

    def reset(self):
        Store.objects.all().delete()

    def get_key(self, classifier, key, default=None):
        try:
            obj = Store.objects.filter(classifier=classifier, key=key)[0]
            value = json.loads(obj.value)
        except (IndexError, Store.DoesNotExist):
            value = default
        return value

    def set_key(self, classifier, key, value):
        value = json.dumps(value)
        try:
            obj = Store.objects.filter(classifier=classifier, key=key)[0]
            obj.value = value
        except (IndexError, Store.DoesNotExist):
            obj = Store.objects.create(
                classifier=classifier, key=key, value=value)
        obj.save()

    def set_key_list(self, classifier, key_value_tuples):
        for key, value in key_value_tuples:
            self.set_key(classifier, key, value)


TOKEN_RE = re.compile(r'\W')


def tokenize(text):
    """Takes a piece of text and tokenizes it into train/classify tokens"""
    # FIXME: This is a shite tokenizer and doesn't handle urls
    # well. (We should handle urls well.)
    tokens = TOKEN_RE.split(text)
    return [token.lower() for token in tokens if token]


_cached_spicedham = threading.local()


def get_spicedham():
    """Retrieve a Spicedham object

    These objects are cached threadlocal.
    """
    sham = getattr(_cached_spicedham, 'sham', None)
    if sham is None:
        config = {
            'backend': 'FjordBackend'
        }

        sham = Spicedham(config)
        _cached_spicedham.sham = sham
    return sham


def train_cmd(path, classification):
    """Recreates training data using datafiles in path"""
    path = os.path.abspath(path)

    if not os.path.exists(path):
        raise ValueError('path "%s" does not exist' % path)

    sham = get_spicedham()

    # Wipe existing training data.
    print 'Wiping existing data...'
    sham.backend.reset()

    # Load all data for when classifier=True
    true_path = os.path.join(path, classification)
    print 'Loading classifier=True data from %s...' % true_path
    files = [os.path.join(true_path, fn)
             for fn in os.listdir(true_path) if fn.endswith('.json')]
    print '  %s records...' % len(files)
    for fn in files:
        print '  - ' + fn
        with open(fn, 'r') as fp:
            data = json.load(fp)
        sham.train(tokenize(data['description']), match=True)

    # Load all data for when classifier=False
    false_path = os.path.join(path, 'not_' + classification)
    print 'Loading classifier=False data from %s...' % false_path
    files = [os.path.join(false_path, fn)
             for fn in os.listdir(false_path) if fn.endswith('.json')]
    print '  %s records...' % len(files)
    for fn in files:
        print '  - ' + fn
        with open(fn, 'r') as fp:
            data = json.load(fp)
        sham.train(tokenize(data['description']), match=False)

    print 'Done!'
