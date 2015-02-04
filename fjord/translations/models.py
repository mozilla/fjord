from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.mail import mail_admins
from django.db import models

from dennis.translator import Translator
from statsd import statsd
import waffle

from .gengo_utils import (
    FjordGengo,
    GengoAPIFailure,
    GengoMachineTranslationFailure,
    GengoUnknownLanguage,
    GengoUnsupportedLanguage,
)
from .utils import locale_equals_language
from fjord.base.models import ModelBase
from fjord.base.utils import wrap_with_paragraphs
from fjord.journal.models import Record
from fjord.journal.utils import j_error, j_info


class SuperModel(models.Model):
    """Model used for unit tests

    It's really difficult to define a model in the test suite used
    just for testing without a lot of shenanigans with South and the
    db, so intead we define a "real" model, but only use it for
    testing.

    """
    locale = models.CharField(max_length=5)
    desc = models.CharField(blank=True, default=u'', max_length=100)
    trans_desc = models.CharField(blank=True, default=u'', max_length=100)


_translation_systems = {}


def get_translation_systems():
    """Returns translation systems map

    """
    return _translation_systems


def get_translation_system_choices():
    """Returns a tuple of (value, display-name) tuples for Choices field

    This inserts a "no choice" choice at the beginning, too, the value of
    which is the empty string.

    """
    choices = [(key, key) for key in _translation_systems.keys()]
    choices.insert(0, (u'', u'None'))
    return tuple(choices)


class TranslationSystemMeta(type):
    """Metaclass to register TranslationSystem subclasses"""
    def __new__(cls, name, bases, attrs):
        new_cls = super(TranslationSystemMeta, cls).__new__(
            cls, name, bases, attrs)
        if new_cls.name:
            _translation_systems[new_cls.name] = new_cls
        return new_cls


class TranslationSystem(object):
    """Translation system base class

    All translation system plugins should subclass this. They should
    additionally do the following:

    1. set the name property to something unique
    2. implement translate method

    See FakeTranslator and DennisTranslator for sample
    implementations.

    """
    __metaclass__ = TranslationSystemMeta

    # Name of this translation system
    name = ''

    # Whether or not this system uses push and pull translations
    use_push_and_pull = False

    # Whether or not this system has daily activities
    use_daily = False

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        """Implement this to translation fields on an instance

        This translates in-place.

        If this is an asynchronous system, then this can either push
        the text to be translated now or queue the text to be pushed
        later in a batch of things to be translated.

        """
        raise NotImplementedError()

    def push_translations(self):
        """Implement this to do any work required to push translations

        This is for asynchronous systems that take a batch of translations,
        perform some work, and then return results some time later.

        Print any status text to stdout.

        """
        raise NotImplementedError()

    def pull_translations(self):
        """Implement this to do any work required to pull translations

        This is for asynchronous systems that take a batch of translations,
        perform some work, and then return results some time later.

        Print any status text to stdout.

        """
        raise NotImplementedError()

    def run_daily_activities(self):
        """Implement this to do any work that needs to happen once per day

        Examples:

        1. sending out daily reminders
        2. sending out a warning about low balance

        Print any status text to stdout.

        """
        raise NotImplementedError()

    def log_info(self, instance, action='translate', msg=u'', metadata=None):
        metadata = metadata or {}

        j_info(
            app='translations',
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata=metadata
        )

    def log_error(self, instance, action='translate', msg=u'', metadata=None):
        metadata = metadata or {}

        j_error(
            app='translations',
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata=metadata
        )


# ---------------------------------------------------------
# Fake translation system
# ---------------------------------------------------------

class FakeTranslator(TranslationSystem):
    """Translates by uppercasing text"""
    name = 'fake'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        setattr(instance, dst_field, getattr(instance, src_field).upper())
        instance.save()
        self.log_info(instance=instance, action='translate', msg='success')


# ---------------------------------------------------------
# Dennis translation system
# ---------------------------------------------------------

class DennisTranslator(TranslationSystem):
    """Translates using shouty and anglequote"""
    name = 'dennis'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        text = getattr(instance, src_field)
        if text:
            pipeline = ['shouty', 'anglequote']
            translated = Translator([], pipeline).translate_string(text)
            setattr(instance, dst_field, translated)
            instance.save()
            self.log_info(instance=instance, action='translate', msg='success')


# ---------------------------------------------------------
# Gengo machine translator system AI 9000 of doom
# ---------------------------------------------------------

class GengoMachineTranslator(TranslationSystem):
    """Translates using Gengo machine translation"""
    name = 'gengo_machine'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        # If gengosystem is disabled, we just return immediately. We
        # can backfill later.
        if not waffle.switch_is_active('gengosystem'):
            return

        text = getattr(instance, src_field)
        metadata = {
            'locale': instance.locale,
            'length': len(text),
            'body': text[:50].encode('utf-8')
        }

        gengo_api = FjordGengo()
        try:
            lc_src = gengo_api.guess_language(text)
            if lc_src not in gengo_api.get_languages():
                raise GengoUnsupportedLanguage(
                    'unsupported language: {0}'.format(lc_src))

            if not locale_equals_language(instance.locale, lc_src):
                # Log this for metrics-purposes
                self.log_error(
                    instance,
                    action='guess-language',
                    msg='locale "{0}" != guessed language "{1}"'.format(
                        instance.locale, lc_src),
                    metadata=metadata)

            if locale_equals_language(dst_lang, lc_src):
                # If the source language is english, we just copy it over.
                setattr(instance, dst_field, text)
                instance.save()
                self.log_info(
                    instance, action='translate',
                    msg=u'lc_src == dst_lang, so we copy src to dst',
                    metadata=metadata)
                return

            translated = gengo_api.machine_translate(
                instance.id, lc_src, dst_lang, text)

            if translated:
                setattr(instance, dst_field, translated)
                instance.save()
                self.log_info(instance, action='translate', msg='success',
                              metadata=metadata)
                statsd.incr('translation.gengo_machine.success')

            else:
                self.log_error(instance, action='translate',
                               msg='did not translate', metadata=metadata)
                statsd.incr('translation.gengo_machine.failure')

        except GengoUnknownLanguage as exc:
            # FIXME: This might be an indicator that this response is
            # spam. At some point p, we can write code to account for
            # that.
            self.log_error(instance, action='guess-language', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unknown')

        except GengoUnsupportedLanguage as exc:
            # FIXME: This is a similar boat to GengoUnknownLanguage
            # where for now, we're just going to ignore it because I'm
            # not sure what to do about it and I'd like more data.
            self.log_error(instance, action='translate', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unsupported')

        except (GengoAPIFailure, GengoMachineTranslationFailure):
            # FIXME: For now, if we have a machine translation
            # failure, we're just going to ignore it and move on.
            self.log_error(instance, action='translate', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.failure')


# ---------------------------------------------------------
# Gengo human translator system
# ---------------------------------------------------------

STATUS_CREATED = 'created'
STATUS_IN_PROGRESS = 'in-progress'
STATUS_COMPLETE = 'complete'

STATUS_CHOICES = (
    (STATUS_CREATED, STATUS_CREATED),
    (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
    (STATUS_COMPLETE, STATUS_COMPLETE)
)


class GengoJob(ModelBase):
    """Represents a job for the Gengo human translation system"""
    # Generic foreign key to the instance this record is about
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    # Source and destination fields for the translation
    src_field = models.CharField(max_length=50)
    dst_field = models.CharField(max_length=50)

    # Source and destination languages
    src_lang = models.CharField(default=u'', blank=True, max_length=10)
    dst_lang = models.CharField(default=u'', blank=True, max_length=10)

    # Status of the job and the order it's tied to
    status = models.CharField(
        choices=STATUS_CHOICES, default=STATUS_CREATED, max_length=12)
    order = models.ForeignKey('translations.GengoOrder', null=True)

    # When this job instance was created
    created = models.DateTimeField(default=datetime.now())

    # When this job instance was completed
    completed = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'<GengoJob {0}>'.format(self.id)

    def save(self, *args, **kwargs):
        super(GengoJob, self).save(*args, **kwargs)

        if not self.pk:
            self.log('create GengoJob', {})

    @classmethod
    def unique_id_to_id(self, unique_id):
        parts = unique_id.split('||')
        return int(parts[-1])

    @property
    def unique_id(self):
        """Returns a unique id for this job for this host

        When we create a job with Gengo, we need to tie that job
        uniquely back to a GengoJob row, but that could be created on
        a variety of systems. This (attempts to) create a unique
        identifier for a specific GengoJob in a specific environment
        by (ab)using the SITE_URL.

        FIXME: It's possible we don't need to do this because jobs are
        tied to orders and order numbers are generated by Gengo and
        should be unique.

        """
        return '||'.join([
            getattr(settings, 'SITE_URL', 'localhost'),
            'GengoJob',
            str(self.pk)
        ])

    def assign_to_order(self, order):
        """Assigns the job to an order which makes the job in progress"""
        self.order = order
        self.status = STATUS_IN_PROGRESS
        self.save()

    def mark_complete(self):
        """Marks a job as complete"""
        self.status = STATUS_COMPLETE
        self.completed = datetime.now()
        self.save()
        self.log('completed', {})

    def log(self, action, metadata):
        j_info(
            app='translations',
            src='gengo_human',
            action=action,
            msg='job event',
            instance=self,
            metadata=metadata
        )

    @property
    def records(self):
        return Record.objects.records(self)


class GengoOrder(ModelBase):
    """Represents a Gengo translation order which contains multiple jobs"""
    order_id = models.CharField(max_length=100)
    status = models.CharField(
        choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS, max_length=12)

    # When this instance was created which should also line up with
    # the time the order was submitted to Gengo
    created = models.DateTimeField(default=datetime.now())

    # When this order was completed
    completed = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'<GengoOrder {0}>'.format(self.id)

    def save(self, *args, **kwargs):
        super(GengoOrder, self).save(*args, **kwargs)

        if not self.pk:
            self.log('create GengoOrder', {})

    def mark_complete(self):
        """Marks an order as complete"""
        self.status = STATUS_COMPLETE
        self.completed = datetime.now()
        self.save()
        self.log('completed', {})

    def completed_jobs(self):
        return self.gengojob_set.filter(status=STATUS_COMPLETE)

    def outstanding_jobs(self):
        return self.gengojob_set.exclude(status=STATUS_COMPLETE)

    def log(self, action, metadata):
        j_info(
            app='translations',
            src='gengo_human',
            action=action,
            msg='order event',
            instance=self,
            metadata=metadata
        )

    @property
    def records(self):
        return Record.objects.records(self)


class GengoHumanTranslator(TranslationSystem):
    """Translates using Gengo human translation

    Note: This costs real money!

    """
    name = 'gengo_human'
    use_push_and_pull = True
    use_daily = True

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        # If gengosystem is disabled, we just return immediately. We
        # can backfill later.
        if not waffle.switch_is_active('gengosystem'):
            return

        text = getattr(instance, src_field)
        metadata = {
            'locale': instance.locale,
            'length': len(text),
            'body': text[:50].encode('utf-8')
        }

        gengo_api = FjordGengo()

        # Guess the language. If we can't guess the language, then we
        # don't create a GengoJob.
        try:
            lc_src = gengo_api.guess_language(text)
            if not locale_equals_language(instance.locale, lc_src):
                # Log this for metrics purposes
                self.log_error(
                    instance,
                    action='guess-language',
                    msg='locale "{0}" != guessed language "{1}"'.format(
                        instance.locale, lc_src),
                    metadata=metadata)

        except GengoUnknownLanguage as exc:
            # FIXME: This might be an indicator that this response is
            # spam. At some point p, we can write code to account for
            # that.
            self.log_error(instance, action='guess-language', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unknown')
            return

        except GengoUnsupportedLanguage as exc:
            # FIXME: This is a similar boat to GengoUnknownLanguage
            # where for now, we're just going to ignore it because I'm
            # not sure what to do about it and I'd like more data.
            self.log_error(instance, action='translate', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unsupported')
            return

        # If the source language is english, we just copy it over.
        if locale_equals_language(dst_lang, lc_src):
            setattr(instance, dst_field, text)
            instance.save()
            self.log_info(
                instance, action='translate',
                msg=u'lc_src == dst_lang, so we copy src to dst',
                metadata=metadata)
            return

        # If the src -> dst isn't a supported pair, log an issue for
        # metrics purposes and move on.
        if (lc_src, dst_lang) not in gengo_api.get_language_pairs():
            self.log_error(
                instance, action='translate',
                msg=u'(lc_src {0}, dst_lang {1}) not supported'.format(
                    lc_src, dst_lang),
                metadata=metadata)
            return

        job = GengoJob(
            content_object=instance,
            src_lang=lc_src,
            src_field=src_field,
            dst_lang=dst_lang,
            dst_field=dst_field
        )
        job.save()

    def balance_good_to_continue(self, balance, threshold):
        """Checks whether balance is good to continue

        If it's not, this sends some mail and returns False.

        We check against a threshold that's high enough that we're
        pretty sure the next job we create will not exceed the credits
        in the account. Pretty sure if we exceed the credits in the
        account, it'll return a non-ok opstat and that'll throw an
        exception and everything will be ok data-consistency-wise.

        """
        # FIXME: This should email a different group than admin,
        # but I'm (ab)using the admin group for now because I know
        # they're set up right.
        if balance < threshold:
            mail_admins(
                subject='Gengo account balance {0} < {1}'.format(
                    balance, threshold),
                message=wrap_with_paragraphs(
                    'Dagnabit! Send more money or the translations get it! '
                    'Don\'t try no funny business, neither!'
                    '\n\n'
                    'Love,'
                    '\n\n'
                    'Fjord McGengo'
                )
            )
            return False

        return True

    def push_translations(self):
        # If gengosystem is disabled, we just return immediately. We
        # can backfill later.
        if not waffle.switch_is_active('gengosystem'):
            return

        gengo_api = FjordGengo()

        if not gengo_api.is_configured():
            # If Gengo isn't configured, then we drop out here rather
            # than raise a GengoConfig error.
            return

        balance = gengo_api.get_balance()
        threshold = settings.GENGO_ACCOUNT_BALANCE_THRESHOLD

        # statsd the balance so we can track it with graphite
        statsd.gauge('translation.gengo.balance', balance)

        if not self.balance_good_to_continue(balance, threshold):
            # If we don't have enough balance, stop.
            return

        # Create language buckets for the jobs
        jobs = GengoJob.objects.filter(status=STATUS_CREATED)
        lang_buckets = {}
        for job in jobs:
            lang_buckets.setdefault(job.src_lang, []).append(job)

        # For each bucket, assemble and order and post it.
        for lang, jobs in lang_buckets.items():
            batch = []
            for job in jobs:
                batch.append({
                    'id': job.id,
                    'lc_src': job.src_lang,
                    'lc_dst': job.dst_lang,
                    'text': getattr(job.content_object, job.src_field),
                    'unique_id': job.unique_id
                })

            # This will kick up a GengoAPIFailure which has the
            # complete response in the exception message. We want that
            # to propagate that and end processing in cases where
            # something bad happened because then we can learn more
            # about the state things are in. Thus we don't catch
            # exceptions here.
            resp = gengo_api.human_translate_bulk(batch)

            # We should have an order_id at this point, so we create a
            # GengoOrder with it.
            order = GengoOrder(order_id=resp['order_id'])
            order.save()
            order.log('created', metadata={'response': resp})

            # Persist the order on all the jobs and change their
            # status.
            for job in jobs:
                job.assign_to_order(order)

            # Update the balance and see if we're below the threshold.
            balance = balance - float(resp['credits_used'])

            if not self.balance_good_to_continue(balance, threshold):
                # If we don't have enough balance, stop.
                return

    def pull_translations(self):
        # If gengosystem is disabled, we just return immediately. We
        # can backfill later.
        if not waffle.switch_is_active('gengosystem'):
            return

        gengo_api = FjordGengo()

        if not gengo_api.is_configured():
            # If Gengo isn't configured, then we drop out here rather
            # than raise a GengoConfig error.
            return

        # Get all the orders that are in progress
        orders = GengoOrder.objects.filter(status=STATUS_IN_PROGRESS)
        for order in orders:
            # Get the list of all completed jobs
            completed = gengo_api.completed_jobs_for_order(order.order_id)

            # If there are no completed jobs, then we don't need to
            # bother doing any additional processing for this order
            if not completed:
                continue

            # For each complete job we haven't seen before, pull it
            # from the db, save the translated text and update all the
            # bookkeeping.
            for comp in completed:
                id_ = GengoJob.unique_id_to_id(comp['custom_data'])

                job = GengoJob.objects.get(pk=id_)
                if job.status == STATUS_COMPLETE:
                    continue

                instance = job.content_object
                setattr(instance, job.dst_field, comp['body_tgt'])
                instance.save()

                job.mark_complete()

            # Check to see if there are still outstanding jobs for
            # this order. If there aren't, close the order out.
            outstanding = (GengoJob.objects
                           .filter(order=order, status=STATUS_IN_PROGRESS)
                           .count())

            if outstanding == 0:
                order.mark_complete()

    def run_daily_activities(self):
        # If gengosystem is disabled, we don't want to do anything.
        if not waffle.switch_is_active('gengosystem'):
            return

        gengo_api = FjordGengo()

        if not gengo_api.is_configured():
            # If Gengo isn't configured, then we drop out here rather
            # than raise a GengoConfig error.
            return

        balance = gengo_api.get_balance()
        threshold = settings.GENGO_ACCOUNT_BALANCE_THRESHOLD

        if threshold < balance < (2 * threshold):
            mail_admins(
                subject='Warning: Gengo account balance {0} < {1}'.format(
                    balance, 2 * threshold),
                message=wrap_with_paragraphs(
                    'Dear mom,'
                    '\n\n'
                    'Translations are the fab. Running low on funds. Send '
                    'more money when you get a chance.'
                    '\n\n'
                    'Love,'
                    '\n\n'
                    'Fjord McGengo'
                )
            )
