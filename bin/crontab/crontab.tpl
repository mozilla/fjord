#
# {{ header }}
#

MAILTO=input-tracebacks@mozilla.com

HOME=/tmp

# Once a day at 3:00am run the translation daily activites and hb health check
0 3 * * * {{ user }} cd {{ source }} && {{ python }} manage.py translation_daily -v 0 --traceback
0 3 * * * {{ user }} cd {{ source }} && {{ python }} manage.py hbhealthcheck -v 0 --traceback

# Every hour, sync translations. This pulls and pushes to the various
# translation systems.
0 * * * * {{ user }} cd {{ source }} && {{ python }} manage.py translation_sync -v 0 --traceback

# On Sundays at 3:10am, purge data per our data retention policies.
10 3 * * 0 {{ user }} cd {{ source }} && {{ python }} manage.py purge_data -v 3 --traceback
