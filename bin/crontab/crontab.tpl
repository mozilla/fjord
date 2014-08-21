#
# {{ header }}
#

MAILTO=input-tracebacks@mozilla.com

HOME=/tmp

# Once a day at 2:00am run the l10n completion script.
# Note: This runs as root so it has access to the locale/ directory
# to do an svn up.
10 2 * * * root cd {{ source }} && (./bin/run_l10n_completion.sh {{ source }} {{ python }} > /dev/null)

# Every hour, sync translations. This pulls and pushes to the various
# translation systems.
0 * * * * {{ user }} cd {{ source }} && {{ python }} manage.py translation_sync -v 0 --traceback

# On Sundays at 3:10am
10 3 * * 0 {{ user }} cd {{ source }} && {{ python }} manage.py purge_data -v 3 --traceback
