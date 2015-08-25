from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

from fjord.base.urlresolvers import reverse_lazy
from fjord.base.utils import (
    analyzer_required,
    check_new_user
)
from fjord.suggest.providers.trigger.forms import TriggerRuleForm
from fjord.suggest.providers.trigger.models import TriggerRule


class TriggerRuleListView(ListView):
    model = TriggerRule

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(TriggerRuleListView, self).dispatch(*args, **kwargs)


class TriggerRuleCreateView(CreateView):
    model = TriggerRule
    form_class = TriggerRuleForm
    success_url = reverse_lazy('triggerrules')

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(TriggerRuleCreateView, self).dispatch(*args, **kwargs)


class TriggerRuleUpdateView(UpdateView):
    model = TriggerRule
    form_class = TriggerRuleForm
    success_url = reverse_lazy('triggerrules')

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(TriggerRuleUpdateView, self).dispatch(*args, **kwargs)
