import datetime
import dateutil
import iso8601
import hashlib
import logging

def sizeof_fmt(num):
    """
    >>> sizeof_fmt(1024)
    '1 KB'
    """
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')

def fuzzy_to_datetime(fuzzy):
    flen = len(fuzzy)
    if flen == 4 and fuzzy.isdigit():
        dt = datetime.datetime(year=int(fuzzy), month=1, day=1, microsecond=111111)

    elif flen == 7:
        y, m = fuzzy.split('-')
        dt = datetime.datetime(year=int(y), month=int(m), day=1, microsecond=222222)

    elif flen == 10:
        y, m, d = fuzzy.split('-')
        dt = datetime.datetime(year=int(y), month=int(m), day=int(d), microsecond=333333)
    
    elif flen >= 19:
        dt = iso8601.parse_date(fuzzy)

    else:
        raise ValueError("Unable to parse fuzzy date: %s" % fuzzy)

    return dt

def datetime_to_fuzzy(dt):
    ms = str(dt.microsecond)
    flag1 = ms == '111111'
    flag2 = ms == '222222'
    flag3 = ms == '333333'
    
    is_first = dt.day == 1
    is_jan1 = dt.month == 1 and is_first

    if flag1 and is_jan1:
        return str(dt.year)

    if flag2 and is_first:
        return dt.strftime("%Y-%m")

    if flag3:
        return dt.strftime("%Y-%m-%d")

    return dt.isoformat()

def do_hash(filename):
    """
    Perform a hash on the file before uploading. Done in chunks so not to take
    up too much memory.
    """
    logging.info("Hashing...")
    sha256 = hashlib.sha256()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
             sha256.update(chunk)
    logging.info("... Complete")
    return sha256.hexdigest()

if __name__ == '__main__':
    assert fuzzy_to_datetime('2001').isoformat() == '2001-01-01T00:00:00.111111'
    assert fuzzy_to_datetime('1981-05').isoformat() == '1981-05-01T00:00:00.222222'
    assert fuzzy_to_datetime('2012-02-04').isoformat() == '2012-02-04T00:00:00.333333'
    assert fuzzy_to_datetime('2010-11-11T03:12:03Z').isoformat() == '2010-11-11T03:12:03+00:00'

    exact = datetime.datetime(year=2001, month=1, day=1, microsecond=231)
    assert datetime_to_fuzzy(exact) == exact.isoformat()

    assert datetime_to_fuzzy(datetime.datetime(year=2001, month=1, day=1, microsecond=111111)) == '2001'
    assert datetime_to_fuzzy(datetime.datetime(year=2001, month=3, day=1, microsecond=222222)) == '2001-03'
    assert datetime_to_fuzzy(datetime.datetime(year=2001, month=6, day=6, microsecond=333333)) == '2001-06-06'

    assert datetime_to_fuzzy(fuzzy_to_datetime('2002')) == '2002'
    assert datetime_to_fuzzy(fuzzy_to_datetime('2002-05')) == '2002-05'
    assert datetime_to_fuzzy(fuzzy_to_datetime('2002-02-13')) == '2002-02-13'
    assert datetime_to_fuzzy(fuzzy_to_datetime('2010-11-11T03:12:03.293856+00:00')) == '2010-11-11T03:12:03.293856+00:00'
