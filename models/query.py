from utils import is_date_key, fuzzy_to_datetime
from sqlalchemy import not_

from LQL import Query as BaseQuery

class Query(BaseQuery):
    """
    Subclass of LQL.Query that has methods specific to executing queries
    """
    def do_match(key, value):
        """
        Handle the 'matching' operator. Returned is a query clause that gets injected
        into sqlalchemy's filter command.
        """
        if key == 'mimetype' and value.endswith("/*"):
            front_part, _ = value.split("/*")
            return MetaData.value.startswith(front_part) == value

    def execute_query(library):
        """
        Run this query against the given library and return all the matching items.
        """
        from models import MetaData, Item

        for polarity, subclause in self.as_list:
            for key, operator, value in subclause:
                if is_date_key(key):
                    value = fuzzy_to_datetime(value)

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