def compile_query(s):
    """
    Turn a string LQL query into a dict object.
    """
    out = {}
    for item in s.split(';'):
        if '=' in item:
            key, value = item.split("=")
            method = "exact"

        if '>' in item:
            key, value = item.split(">")
            method = "greater"

        if '<' in item:
            key, value = item.split("<")
            method = "less"

        out[key.strip()] = [value.strip(), method]

    return out