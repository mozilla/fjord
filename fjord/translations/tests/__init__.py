def fakeinstance(fields=None, translate_with=lambda x: None, **kwargs):
    """Generates a FakeModel instance with the right bits for translation

    The translation system needs an object with:

    1. a Translation class property that has the source and destination fields
    2. a translate_with function that takes the instance and returns the
       system to translate with
    3. a save function that takes the instance and saves it to the db, though
       we don't want this saving to the db, so we make it a no-op

    """
    class FakeModel(object):
        def __init__(self):
            for key, val in kwargs.items():
                setattr(self, key, val)

            self.translate_with = translate_with
            self.Translation.fields = fields

        class Translation(object):
            pass

        def save(self):
            pass

    return FakeModel()
