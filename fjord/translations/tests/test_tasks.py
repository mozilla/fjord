from nose.tools import eq_

from ..models import SuperModel
from ..tasks import translate_tasks_by_id_list
from fjord.base.tests import TestCase


class TranslateTasksByIdListTestCase(TestCase):
    def test_one(self):
        """Test the basic case"""
        model_path = SuperModel.__module__ + '.' + SuperModel.__name__

        obj = SuperModel(locale='br', desc=u'This is a test string')
        obj.save()

        # Verify no translation, yet
        eq_(obj.trans_desc, u'')
        translate_tasks_by_id_list.delay(model_path, [obj.id])

        # Fetch the object from the db to verify it's been translated.
        obj = SuperModel.objects.get(id=obj.id)
        
        eq_(obj.trans_desc, u'THIS IS A TEST STRING')

    def test_many(self):
        model_path = SuperModel.__module__ + '.' + SuperModel.__name__

        objs = []
        for i in range(50):
            obj = SuperModel(locale='br', desc=u'string %d' % i)
            obj.save()
            objs.append(obj)
        
        translate_tasks_by_id_list.delay(model_path, [obj.id for obj in objs])

        for obj in objs:
            obj = SuperModel.objects.get(id=obj.id)
            # Note: The fake translation just uppercases things. We're
            # abusing inner knowledge of that here.
            eq_(obj.trans_desc, obj.desc.upper())
