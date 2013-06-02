from pyparsing import Word, alphanums,oneOf, Group, QuotedString, delimitedList

from utils import is_date_key, fuzzy_to_datetime
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
    from models import MetaData, Item, BUILT_IN

    query_clauses = query
    if hasattr(query, 'lower'):
        query_clauses = parse_query(query.lower())

    for polarity, subclause in query_clauses:
        for key, operator, value in subclause:
            if is_date_key(key):
                value = fuzzy_to_datetime(value)

            if key in BUILT_IN:
                if operator == 'exact':
                    db_clause = getattr(Item, key) == value
                elif operator in ['after', 'greaterthan']:
                    db_clause = getattr(Item, key) > value
                elif operator in ['before', 'lessthan']:
                    db_clause = getattr(Item, key) < value
                else:
                    raise NotImplementedError("no other operators implemented yet")
            else:
                db_clause = MetaData.key == key
                if operator == 'exact':
                    db_clause = MetaData.value == value and db_clause
                elif operator in ['after', 'greaterthan']:
                    db_clause = MetaData.value > value and db_clause
                elif operator in ['before', 'lessthan']:
                    db_clause = MetaData.value < value and db_clause
                else:
                    raise NotImplementedError("no other operators implemented yet")

            if polarity == 'including':
                items = items.filter(db_clause)
            elif polarity == 'excluding':
                items = items.filter(not_(db_clause))

    return items

def parse_query(s):
    """
    Turn a string LQL query into a "list of lists" object for easier handling.
    """
    identifier = Word("_"+"."+alphanums)
    polarity = oneOf("including excluding", caseless=True)
    operator = oneOf("after exact = == matches lessthan greaterthan after before is_present", caseless=True)
    value = QuotedString("'") | QuotedString('"') | identifier
    key = identifier

    subclause = Group(key + operator + value)
    clause = Group(polarity + Group(delimitedList(subclause, delim=',')))

    LQL = delimitedList(clause, delim=';')
    parsed_obj = LQL.parseString(s)

    parsed_native = eval(str(parsed_obj))
    return parsed_native

if __name__ == '__main__':
    
    cases = [
        [    
            'including mime.type == "video/*"',
            [['including', [['mime.type', '==', 'video/*']]]]
        ],
        [
            "EXCLUDING mimetype ExAcT 'text/plain', key exact 'string value'",
            [['excluding', [['mimetype', 'exact', 'text/plain'], ['key', 'exact', 'string value']]]]
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
        assert parsed == result, msg
        #execute_query(None, parsed)

    print "All tests pass"