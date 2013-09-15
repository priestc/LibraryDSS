from boto.s3.connection import S3Connection
from giotto.utils import random_string

def get_bucket_name(username, domain, aws_key, aws_secret):
    """
    Create a bucket for the usage of LibraryDSS.
    Returned is the name of that bucket.
    """
    conn = S3Connection(aws_key, aws_secret)
    try:
        bucket = conn.create_bucket("lib_%s_%s" % (username, domain))
    except:
        bucket = conn.create_bucket("lib_%s_%s_%s" % (username, domain, random_string(3)))

    return bucket.name