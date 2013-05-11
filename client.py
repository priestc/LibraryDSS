import base64
import datetime
import json
import os
import pickle
import requests
import mimetypes
import logging

import tomlpython

from giotto.primitives import ALL_DATA

from giotto_s3.upload import upload as upload_s3
from giotto_dropbox.upload import upload as upload_dropbox
from giotto_google.upload import upload as upload_google_drive

from utils import do_hash

def query(query):
    with open(".library_identity.example") as identity_file:
        identity = identity_file.read().strip()
    q = {'query': query}
    identity_user, identity_url = identity.split('@')
    url = "http://%s/items.json" % identity_url
    response = requests.get(url, params=q, auth=(identity_user, ''))
    return json.tool(response.json)


def publish(filename, metadata=ALL_DATA):
    """
    Upload the following filename to the library server.
    filename can be either a filename on the local filesystem, or a url.
    giotto publish /path/to/file.jpg --key=value --another=value
    giotto publish http://imgur.com/wd72g4n --key=value
    """
    t0 = datetime.datetime.now()

    with open(".library_identity.example") as datafile:
        identity = datafile.read().strip()
    
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
        hash =  do_hash(filename)
        ext = filename.split('.')[-1]
        f.seek(0)
        logging.warn("File is: %s.%s.%s" % (size, hash, ext))
        url = _upload_to_engine(identity, filename, size, hash)

        if 'date_created' not in metadata:
            metadata['date_created'] = created

        if 'mimetype' not in metadata:
            metadata['mimetype'] = mimetypes.guess_type(filename)

    _complete_publish(identity, size, hash, url, metadata)
    return "Publish Complete. Took %s" % (datetime.datetime.now() - t0)

def _upload_to_engine(identity, filename, size, hash):
    """
    Call the server, get the engine info, then proceed to do the upload.
    Afterwords, return the url of the newly uploaded file.
    """
    data = {"size": size, "hash": hash}
    url = "http://%s/startPublish" % identity

    try:
        response = requests.post(url, data=data, auth=(identity, ''))
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to Library Server: %s" % url)

    code = response.status_code
    if code != 200:
        msg = response.error
        raise Exception("Library Server Error: (%s) %s" % (code, msg))

    ext = filename.split('.')[-1]
    endfilename = "%s.%s.%s" % (size, hash, ext)

    for engine in response.json:
        # engine data is transmitted as a base64 encoded pickle.
        connect_data = pickle.loads(base64.b64decode(engine['data']))
        name = engine['name']
        id = engine['id']
        
        try:
            if name == 's3':
                return id, upload_s3(filename, endfilename, connect_data)

            if name == 'googledrive':
                return id, upload_google_drive(filename, endfilename, connect_data)

            if name == 'dropbox':
                return id, upload_dropbox(filename, endfilename, connect_data)
        except Exception as exc:
            print "upload to %s failed: %s" % (name, exc)

    raise Exception("Upload failed.")

def _complete_publish(identity, size, hash, url, metadata):
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

    print "right before client sends upload details back to finishPublish", metadata
    response = requests.post("http://%s/completePublish" % identity, data=metadata, auth=(identity, ''))
    print "Library server response...", response.content

def is_url(url):
    return url.startswith('http')