import json


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
            continue

        escape = False

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


def build_match(field, token):
    return {'match': {field: token}}


def build_match_phrase(field, token):
    return {'match_phrase': {field: token}}


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
