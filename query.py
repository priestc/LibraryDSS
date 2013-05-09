def compile_query(s):
    """
    Turn a string LQL query into a dict object for more easier
    filtering.
    """
    out = []
    for clause in s.split(';'):
        clause = clause.strip()
        polarity, key, operator = clause.split(' ')[:3]
        value = " ".join(clause.split(' ')[3:])

        wrapped_in_quoted = (
            (value.startswith('"') and value.endswith('"')) or 
            (value.startswith("'") and value.endswith("'"))
        ) 
        if wrapped_in_quoted:
            value = value[1:][:-1]

        out.append([polarity, key, operator, value])

    return out