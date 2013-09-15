import logging
import datetime

import math
import mimetypes
from multiprocessing import Pool
import os

from boto.s3.connection import S3Connection
from filechunkio import FileChunkIO
from models.utils import sizeof_fmt

def _upload_part(bucketname, aws_key, aws_secret, multipart_id, part_num, total_parts, source_path, offset, bytes, amount_of_retries=10):
    """
    Uploads a part with retries.
    """
    def _upload(retries_left=amount_of_retries):
        t0 = datetime.datetime.now()
        try:
            logging.warning('Starting part #%d ...' % part_num)
            conn = S3Connection(aws_key, aws_secret)
            bucket = conn.get_bucket(bucketname)
            for mp in bucket.get_all_multipart_uploads():
                if mp.id == multipart_id:
                    with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
                        mp.upload_part_from_file(fp=fp, part_num=part_num)
                    break
        except Exception:
            delta = datetime.datetime.now() - t0
            duration = str(delta)[:7] # remove microseconds
            if retries_left:
                msg = '... Failed part #%d (after %s), Restarting' % (part_num, duration)
                logging.warning(msg)
                _upload(retries_left=retries_left - 1)
            else:
                msg = '... Failed part #%d (after %s), (Too many retries)' % (part_num, duration)
                logging.warning(msg)
                raise
        else:
            delta = datetime.datetime.now() - t0
            speed = "%s/sec" % sizeof_fmt(float(bytes) / delta.seconds)
            duration = str(delta)[:7] # remove microseconds
            percent = part_num / float(total_parts)
            msg = '... Finished part #%d (took %s, %s) (%.2f%% done)' % (part_num, duration, speed, percent)
            logging.warning(msg)
 
    _upload()


def upload(source_path, keyname, engine):
    """
    Parallel multipart upload. from http://www.topfstedt.de/weblog/?p=558
    """
    headers = {}
    aws_key = engine['aws_key']
    aws_secret = engine['aws_secret']
    bucketname = engine['bucket_name']

    conn = S3Connection(aws_key, aws_secret)
    bucket = conn.get_bucket(bucketname)
    parallel_processes = 1

    mtype = mimetypes.guess_type(keyname)[0] or 'application/octet-stream'
    headers.update({'Content-Type': mtype})
 
    mp = bucket.initiate_multipart_upload(keyname, headers=headers)
 
    source_size = os.stat(source_path).st_size
    bytes_per_chunk = 5242880 # 5MB, the limit as per Amazon's documentation

    chunk_amount = int(math.ceil(source_size / float(bytes_per_chunk)))
    
    logging.warning('Will upload in %d chunks, total size: %s' % (chunk_amount, sizeof_fmt(source_size)))

    pool = Pool(processes=parallel_processes)
    for i in range(chunk_amount):
        offset = i * bytes_per_chunk
        remaining_bytes = source_size - offset
        bytes = min([bytes_per_chunk, remaining_bytes])
        part_num = i + 1
        pool.apply_async(_upload_part, [bucketname, aws_key, aws_secret, mp.id,
            part_num, chunk_amount, source_path, offset, bytes])
    pool.close()
    pool.join()
 
    parts_on_mp = len(mp.get_all_parts())
    if parts_on_mp == chunk_amount:
        mp.complete_upload()
        key = bucket.get_key(keyname)
        key.set_acl('public-read')
    else:
        msg = "Canceling Multipart upload, should be %d parts, found %d instead" % (chunk_amount, parts_on_mp)
        logging.error(msg)
        import debug
        mp.cancel_upload()

    return key.generate_url(99).split('?')[0]