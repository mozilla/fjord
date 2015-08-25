_purgers = []


def get_purgers():
    return list(_purgers)


def register_purger(fun):
    _purgers.append(fun)
    return fun


def purge_data(verbose=False):
    """Implements data purging across the project per data retention policy"""
    # We import these here so there's no way we could have circular
    # imports.
    from fjord.journal.utils import j_info  # noqa

    msg = ''

    # For each registered purge function, run it and print output if verbose
    for purger in get_purgers():
        out = purger()
        if verbose:
            print out
        msg = msg + out + '\n'

    # Log all output to the journal
    j_info(app='base',
           src='purge_data',
           action='purge_data',
           msg=msg)
