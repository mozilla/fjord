from math import floor
import json

from django.template.defaultfilters import slugify

from fjord.base.util import epoch_milliseconds


WHITESPACE = u' \t\r\n'


def to_tokens(text):
    """Breaks the search text into tokens"""
    in_quotes = False
    escape = False

    tokens = []
    token = []

    for c in text:
        if c == u'\\':
            escape = True
            token.append(c)
            continue

        if in_quotes:
            if not escape and c == u'"':
                in_quotes = False
            token.append(c)

        elif not escape and c == u'"':
            in_quotes = True
            token.append(c)

        elif c in WHITESPACE:
            if token:
                tokens.append(u''.join(token))
                token = []

        else:
            token.append(c)

        escape = False

    if in_quotes:
        # Finish off a missing quote
        if token:
            token.append(u'"')
        else:
            tokens[-1] = tokens[-1] + u'"'

    if token:
        # Add last token
        tokens.append(u''.join(token))

    return tokens


class ParseError(Exception):
    pass


def unescape(text):
    """Unescapes text

    >>> unescape(u'abc')
    u'abc'
    >>> unescape(u'\\abc')
    u'abc'
    >>> unescape(u'\\\\abc')
    u'\\abc'

    """
    # Note: We can ditch this and do it in tokenizing if tokenizing
    # returned typed tokens rather than a list of strings.
    new_text = []
    escape = False
    for c in text:
        if not escape and c == u'\\':
            escape = True
            continue

        new_text.append(c)
        escape = False

    return u''.join(new_text)


def build_match(field, token):
    return {'text': {field: unescape(token)}}


def build_match_phrase(field, token):
    return {'text_phrase': {field: unescape(token)}}


def build_or(clauses):
    return {'bool': {'should': clauses, 'minimum_should_match': 1}}


def build_and(clauses):
    return {'bool': {'must': clauses}}


def parse_match(field, tokens):
    """Parses a match or match_phrase node

    :arg field: the field we're querying on
    :arg tokens: list of tokens to consume

    :returns: list of match clauses
    """
    clauses = []
    text = []

    while tokens and tokens[-1] not in (u'OR', u'AND'):
        token = tokens.pop()

        if token.startswith(u'"'):
            if text:
                clauses.append(build_match(field, u' '.join(text)))
                text = []
            clauses.append(build_match_phrase(field, token[1:-1]))
        else:
            text.append(token)

    if text:
        clauses.append(build_match(field, u' '.join(text)))

    return clauses


def parse_oper(field, lhs, tokens):
    """Parses a single bool query

    :arg field: the field we're querying on
    :arg lhs: the clauses on the left hand side
    :arg tokens: list of tokens to consume

    :returns: bool query
    """
    token = tokens.pop()
    rhs = parse_query(field, tokens)

    if token == u'OR':
        lhs.extend(rhs)
        return build_or(lhs)
    elif token == u'AND':
        lhs.extend(rhs)
        return build_and(lhs)

    # Note: This probably will never get reached given the way
    # parse_match slurps. If the code were changed, it's possible this
    # might be triggerable.
    raise ParseError('Not an oper token: {0}'.format(token))


def parse_query(field, tokens):
    """Parses a match or query

    :arg field: the field we're querying on
    :arg tokens: list of tokens to consume

    :returns: list of clauses
    """
    match_clauses = parse_match(field, tokens)
    if tokens:
        return [parse_oper(field, match_clauses, tokens)]
    return match_clauses


def generate_query_parsed(field, text):
    """Parses the search text and returns ES query

    This tries to handle parse errors. If the text is unparseable, it
    returns a match/fuzzy/match_phrase query.

    :arg field: the field to search
    :arg text:  the user's search text

    :return: ES query

    It uses a recursive descent parser with this grammar::

        query = match | match oper
        oper  = "AND" query |
                "OR" query
        match = token ... |
                '"' token '"'

    If it encounters a parse error, it attempts to recover, but if it
    can't, then it just returns a single match query.

    """
    # Build the ES query tree data structure bottom up.
    tokens = to_tokens(text)
    tokens.reverse()

    try:
        clauses = parse_query(field, tokens)
    except ParseError:
        return build_match(field, text)

    if len(clauses) > 1:
        return build_or(clauses)

    return clauses[0]


class JSONDatetimeEncoder(json.JSONEncoder):
    def default(self, value):
        if hasattr(value, 'strftime'):
            return value.isoformat()
        return super(JSONDatetimeEncoder, self).default(value)


def counts_to_options(counts, name, display=None, display_map=None,
                      value_map=None, checked=None):
    """Generates a set of option blocks from a set of facet counts.

    One options block represents a set of options to search for, as
    well as the query parameter that can be used to search for that
    opinion, and the friendly name to show the opinion block as.

    For each option the keys mean:
    - `name`: Used to name in the DOM.
    - `display`: Shown to the user.
    - `value`: The value to set the query parameter to in order to
      search for this option.
    - `count`: The facet count of this option.
    - `checked`: Whether the checkbox should start checked.

    :arg counts: A list of tuples of the form (count, item), like from
        ES.
    :arg name: The name of the search string that corresponds to this
        block.  Like "locale" or "platform".
    :arg display: The human friendly title to represent this set of
        options.
    :arg display_map: Either a dictionary or a function to map items
        to their display names. For a dictionary, the form is {item:
        display}. For a function, the form is lambda item:
        display_name.
    :arg value_map: Like `display_map`, but for mapping the values
        that get put into the query string for searching.
    :arg checked: Which item should be marked as checked.
    """
    if display is None:
        display = name

    options = {
        'name': name,
        'display': display,
        'options': [],
    }

    # This is used in the loop below, to be a bit neater and so we can
    # do it for both value and display generically.
    def from_map(source, item):
        """Look up an item from a source.

        The source may be a dictionary, a function, or None, in which
        case the item is returned unmodified.

        """
        if source is None:
            return item
        elif callable(source):
            return source(item)
        else:
            return source[item]

    # Built an option dict for every item.
    for item, count in counts:
        options['options'].append({
            'name': slugify(item),
            'display': from_map(display_map, item),
            'value': from_map(value_map, item),
            'count': count,
            'checked': checked == item,
        })
    options['options'].sort(key=lambda item: item['count'], reverse=True)
    return options


DAY_IN_MILLIS = 24 * 60 * 60 * 1000.0


def zero_fill(start, end, data_sets, spacing=DAY_IN_MILLIS):
    """Given one or more histogram dicts, zero fill them in a range.

    The format of the dictionaries should be {milliseconds: numeric
    value}. It is important that the time points in the dictionary are
    equally spaced. If they are not, extra points will be added.

    This method works with milliseconds because that is the format
    elasticsearch and Javascript use.

    :arg start: Datetime to start zero filling.
    :arg end: Datetime to stop zero filling at.
    :arg data_sets: A list of dictionaries to zero fill.
    :arg spacing: Number of milliseconds between data points.
    """
    start_millis = epoch_milliseconds(start)
    # Date ranges are inclusive on both ends.
    end_millis = epoch_milliseconds(end) + spacing

    # `timestamp` is a loop counter that iterates over the timestamps
    # from start to end. It can't just be `timestamp = start`, because
    # then the zeros being adding to the data might not be aligned
    # with the data already in the graph, since we aren't counting by
    # 24 hours, and the data could have a timezone offset.
    #
    # This block picks a time up to `spacing` time after `start` so
    # that it lines up with the data. If there is no data, then we use
    # `stamp = start`, because there is nothing to align with.

    # start <= timestamp < start + spacing
    days = [d for d in data_sets if d.keys()]
    if days:
        source = days[0]
        timestamp = source.keys()[0]
        d = floor((timestamp - start_millis) / spacing)
        timestamp -= d * spacing
    else:
        # If there no data, it doesn't matter how it aligns.
        timestamp = start_millis

    # Iterate in the range `start` to `end`, starting from
    # `timestamp`, increasing by `spacing` each time. This ensures
    # there is a data point for each day.
    while timestamp < end_millis:
        for d in data_sets:
            if timestamp not in d:
                d[timestamp] = 0
        timestamp += spacing
