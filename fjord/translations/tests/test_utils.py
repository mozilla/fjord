from fjord.base.tests import TestCase
from fjord.translations import gengo_utils
from fjord.translations.models import SuperModel
from fjord.translations.utils import translate


class TestGeneralTranslate(TestCase):
    def setUp(self):
        gengo_utils.GENGO_LANGUAGE_CACHE = (
            {u'opstat': u'ok',
             u'response': [
                 {u'unit_type': u'word', u'localized_name': u'Espa\xf1ol',
                  u'lc': u'es', u'language': u'Spanish (Spain)'}
             ]},
            (u'es',)
        )

    def test_translate_fake(self):
        obj = SuperModel(locale='br', desc=u'This is a test string')
        obj.save()

        assert obj.trans_desc == u''
        translate(obj, 'fake', 'br', 'desc', 'en', 'trans_desc')
        assert obj.trans_desc == u'THIS IS A TEST STRING'

    def test_translate_dennis(self):
        obj = SuperModel(locale='fr', desc=u'This is a test string')
        obj.save()

        assert obj.trans_desc == u''
        translate(obj, 'dennis', 'br', 'desc', 'en', 'trans_desc')
        assert obj.trans_desc == u'\xabTHIS IS A TEST STRING\xbb'
