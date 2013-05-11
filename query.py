from pyparsing import (Word, alphas, alphanums,oneOf, Keyword, Optional, Group,
    QuotedString, StringEnd, ZeroOrMore, OneOrMore, Suppress, delimitedList)

from utils import is_date_key
from sqlalchemy import not_

def do_match(key, value):
    """
    Handle the 'matching' operator. Returned is a query clause that gets injected
    into sqlalchemy's filter command.
    """
    if key == 'mimetype' and value.endswith("/*"):
        front_part, _ = value.split("/*")
        return MetaData.value.startswith(front_part) == value

def execute_query(items, query):
    """
    Given an LQL query, run that query against the given library and return
    all the matching items.
    """
    from models import MetaData

    query_clauses = query
    if isinstance(query, str):
        query_clauses = compile_query(query.lower())

    for polarity, subclause in query:
        print "--", polarity
        for key, operator, value in subclause:
            print key, operator, value

        if polarity == 'including':
            items = items.filter(MetaData.key == key and db_clause)
        elif polarity == 'excluding':
            items = items.filter(not_(MetaData.key == key and db_clause))

    return items

"""
    is_date = is_date_key(key)
    db_clause = None
        for subclause in clause['subclauses']:
            polarity, operator,
            if operator in ['exact', '=', '==']:
                db_clause = MetaData.value == value
            elif operator in ['before', 'lessthan']:
                db_clause = MetaData.value < value
            elif operator == ['after', 'greaterthan']:
                db_clause = MetaData.value > value
            elif operator == 'matches':
                db_clause = do_match(key, value)
            elif operator == 'is_present':
                db_clause = True

        if polarity == 'including':
            items = items.filter(MetaData.key == key and db_clause)
        elif polarity == 'excluding':
            items = items.filter(not_(MetaData.key == key and db_clause))
        else:
            raise Exception("Invalid polarity clause: %s" % polarity)

    print items.all()
    return items.all()
"""

def parse_query(s):
    """
    Turn a string LQL query into a "list of lists" object for easier handling.
    """
    identifier = Word("_"+"."+alphanums)
    polarity = oneOf("including excluding", caseless=True)
    operator = oneOf("exact = == matches lessthan greaterthan after before", caseless=True)
    value = QuotedString("'") | QuotedString('"') | identifier
    key = identifier

    subclause = Group(key + operator + value)
    clause = Group(polarity + Group(delimitedList(subclause, delim=',')))

    LQL = delimitedList(clause, delim=';')
    return LQL.parseString(s)

if __name__ == '__main__':
    
    cases = [
        [    
            'including mime.type == "video/*"',
            [['including', [['mime.type', '==', 'video/*']]]]
        ],
        [
            "EXCLUDING mimetype ExAcT balls, fart exact 'toot butt'",
            [['excluding', [['mimetype', 'exact', 'balls'], ['fart', 'exact', 'toot butt']]]]
        ],
        [
            'INCLUDING source exact DVD; EXCLUDING date == 2006',
            [["including", [['source', 'exact', 'DVD']]], ['excluding', [['date', '==', '2006']]]]
        ],
        [
            'including source == DVD, date == 2006; excluding mimetype matches  "text/*"',
            [["including", [['source', '==', 'DVD'], ['date', '==', '2006']]],["excluding", [['mimetype', 'matches', 'text/*']]]]
        ]
    ]

    for query, result in cases:
        parsed = parse_query(query)
        msg = "This query: \n\n%s\n\nreturned: \n\n%s\n\ninstead of:\n\n%s" % (query, result, parsed)
        assert str(parsed) == str(result), msg
        execute_query(None, parsed)

    print "All tests pass"