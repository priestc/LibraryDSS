import datetime
import os
import hashlib
import requests
import mimetypes
import logging

import upload_engine
import tomlpython

from giotto.primitives import ALL_DATA

def publish(filename, metadata=ALL_DATA):
    """
    Upload the following filename to the library server.
    filename can be either a filename on the local filesystem, or a url.
    giotto publish /path/to/file.jpg --key=value --another=value
    giotto publish http://imgur.com/wd72g4n --key=value
    """
    t0 = datetime.datetime.now()

    with open("example.library_publish.toml") as datafile:
        settings = tomlpython.parse(datafile)
    
    try:
        f = open(filename, 'r')
    except IOError:
        if is_url(filename):
            url = filename
            size = None
            hash = None
        else:
            raise
    else:
        # upload a local file
        created = datetime.datetime.fromtimestamp(os.stat(filename).st_ctime)
        size = os.stat(filename).st_size
        hash = _do_hash(filename)
        ext = filename.split('.')[-1]
        f.seek(0)
        logging.warn("File is: %s.%s.%s" % (size, hash, ext))
        url = _upload_to_engine(settings, filename, size, hash)

        if 'date_created' not in metadata:
            metadata['date_created'] = created

        if 'mimetype' not in metadata:
            metadata['mimetype'] = mimetypes.guess_type(filename)

    _complete_publish(settings, size, hash, url, metadata)
    return "Publish Complete. Took %s" % (datetime.datetime.now() - t0)

def _do_hash(filename):
    logging.warn("Hashing...")
    sha256 = hashlib.sha256()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
             sha256.update(chunk)
    logging.warn("... Complete")
    return sha256.hexdigest()

def _upload_to_engine(settings, filename, size, hash):
    """
    Call the server, get the engine info, then proceed to do the upload.
    Afterwords, return the url of the newly uploaded file.
    """
    data = {"size": size, "hash": hash}
    client_url = settings['client']['library']['url']
    identity = settings['client']['library']['identity']
    url = "%s/startPublish" % client_url
    response = requests.post(url, data=data, auth=(identity, ''))
    
    code = response.status_code
    if code != 200:
        msg = response.error
        raise Exception("Library Server Error: (%s) %s" % (code, msg))

    url = upload_engine.upload(filename, size, hash, response.json)
    return url

def _complete_publish(settings, size, hash, url, metadata):
    """
    Send the actual URL back to the library server after uploading.
    Or if the user passes in a URL, pass on that url directly.
    """
    if size and hash:
        # local file
        metadata.update({"url": url, "hash": hash, "size": size})
    else:
        # url
        metadata.update({"url": url})

    client_url = settings['client']['library']['url']
    identity = settings['client']['library']['identity']
    print "right before client sends upload details back to finishPublish", metadata
    response = requests.post("%s/completePublish" % client_url, data=metadata, auth=(identity, ''))
    print "Library server response...", response.content

def is_url(url):
    return url.startswith('http')

def configure():
    pass