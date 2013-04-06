import logging
import boto
import requests

import math
import mimetypes
from multiprocessing import Pool
import os
import uuid

from boto.s3.connection import S3Connection
from filechunkio import FileChunkIO

def _upload_part(bucketname, aws_key, aws_secret, multipart_id, part_num,
    source_path, offset, bytes, amount_of_retries=10):
    """
    Uploads a part with retries.
    """
    def _upload(retries_left=amount_of_retries):
        try:
            logging.info('Start uploading part #%d ...' % part_num)
            conn = S3Connection(aws_key, aws_secret)
            bucket = conn.get_bucket(bucketname)
            for mp in bucket.get_all_multipart_uploads():
                if mp.id == multipart_id:
                    with FileChunkIO(source_path, 'r', offset=offset,
                        bytes=bytes) as fp:
                        mp.upload_part_from_file(fp=fp, part_num=part_num)
                    break
        except Exception, exc:
            if retries_left:
                _upload(retries_left=retries_left - 1)
            else:
                logging.info('... Failed uploading part #%d' % part_num)
                raise exc
        else:
            logging.info('... Uploaded part #%d' % part_num)
 
    _upload()
 
 
def upload_s3(bucketname, aws_key, aws_secret, source_path, keyname, headers={}, guess_mimetype=True, parallel_processes=4):
    """
    Parallel multipart upload. from http://www.topfstedt.de/weblog/?p=558
    """
    conn = S3Connection(aws_key, aws_secret)
    bucket = conn.get_bucket(bucketname)

    if guess_mimetype:
        mtype = mimetypes.guess_type(keyname)[0] or 'application/octet-stream'
        headers.update({'Content-Type': mtype})
 
    mp = bucket.initiate_multipart_upload(keyname, headers=headers)
 
    source_size = os.stat(source_path).st_size
    bytes_per_chunk = max(int(math.sqrt(5242880) * math.sqrt(source_size)),
        5242880)
    chunk_amount = int(math.ceil(source_size / float(bytes_per_chunk)))
 
    pool = Pool(processes=parallel_processes)
    for i in range(chunk_amount):
        offset = i * bytes_per_chunk
        remaining_bytes = source_size - offset
        bytes = min([bytes_per_chunk, remaining_bytes])
        part_num = i + 1
        pool.apply_async(_upload_part, [bucketname, aws_key, aws_secret, mp.id,
            part_num, source_path, offset, bytes])
    pool.close()
    pool.join()
 
    if len(mp.get_all_parts()) == chunk_amount:
        mp.complete_upload()
        key = bucket.get_key(keyname)
        key.set_acl('public-read')
    else:
        mp.cancel_upload()

    return key.generate_url(99).split('?')[0]


def upload_google_drive(filename, api_key):
    """
    Upload to googe drive
    """
    return "url"

def upload(filename, size, hash, engine):
    engine = engine[0]
    print engine
    if engine['name'] == 's3':
        endfilename = "%s.%s" % (size, hash)
        return upload_s3(engine['bucket_name'], engine['access_key'], engine['secret_key'], filename, endfilename)

    if engine['name'] == 'googledrive':
        return upload_google_drive(filename, engine.apikey)

    raise Exception("No Storage Engine configured")