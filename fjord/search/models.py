_mapping_types = {}


def register_mapping_type(mapping_type):
    """Registers a mapping type.

    This gives us a way to get all the registered mapping types for
    indexing.

    """
    _mapping_types[mapping_type.get_mapping_type_name()] = mapping_type


def get_mapping_types(mapping_types=None):
    """Returns a dict of name -> mapping type.

    :arg mapping_types: list of mapping type names to restrict
        the dict to.

    """
    if mapping_types is None:
        return _mapping_types

    return dict((key, val) for key, val in _mapping_types.items()
                if key in mapping_types)
