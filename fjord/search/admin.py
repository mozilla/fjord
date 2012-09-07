import logging
from datetime import datetime

from django.contrib import admin
from django.shortcuts import render

import pyes

from fjord.search.index import get_index, get_index_stats, get_indexes


log = logging.getLogger('i.search')


def search_admin_view(request):
    """Render the admin view containing search tools"""
    error_messages = []
    stats = None
    indexes = []

    try:
        # This gets index stats, but also tells us whether ES is in
        # a bad state.
        try:
            stats = get_index_stats()
        except pyes.exceptions.IndexMissingException:
            stats = None
        indexes = get_indexes()
        indexes.sort(key=lambda m: m[0])

    except pyes.urllib3.MaxRetryError:
        error_messages.append('Error: Elastic Search is not set up on this '
                              'machine or is not responding. (MaxRetryError)')
    except pyes.exceptions.IndexMissingException:
        error_messages.append('Error: Index is missing. Press the reindex '
                              'button below. (IndexMissingException)')
    except pyes.urllib3.TimeoutError:
        error_messages.append('Error: Connection to Elastic Search timed out. '
                              '(TimeoutError)')

    return render(request, 'admin/search_admin_view.html', {
            'title': 'Search',
            'mapping_type_stats': stats,
            'indexes': indexes,
            'index': get_index(),
            'error_messages': error_messages,
            'now': datetime.now(),
            })


admin.site.register_view('search-admin-view', search_admin_view,
                         'Search - Index Maintenance')
