from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from mobility.decorators import mobile_template

from fjord.feedback.models import Simple as SimpleFeedback


@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
    page = request.GET.get('page', 1)

    opinion_list = SimpleFeedback.objects.all()
    opinion_count = opinion_list.count()
    opinion_count_happy = opinion_list.filter(happy=True).count()
    opinion_count_sad = opinion_list.filter(happy=False).count()

    paginator = Paginator(opinion_list, 20)
    try:
        opinions = paginator.page(page)
    except PageNotAnInteger:
        opinions = paginator.page(1)
    except EmptyPage:
        if page < 1:
            opinions = paginator.page(1)
        else:
            opinions = paginator.page(paginator.num_pages)

    return render(request, template, {
        'opinions': opinions,
        'opinion_count': opinion_count,
        'opinion_count_happy': opinion_count_happy,
        'opinion_count_sad': opinion_count_sad,
    })
