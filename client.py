import os
import hashlib
import requests

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
        size = os.stat(filename).st_size
        hash = hashlib.md5(f.read()).hexdigest()
        f.seek(0)
        url = upload_to_engine(filename, size, hash)

    complete_publish(size, hash, url, metadata)
    return "Publish Complete"

def upload_to_engine(settings, filename, size, hash):
    """
    Call the server, get the engine info, then proceed to do the upload.
    Afterwords, return the url of the newly uploaded file.
    """
    data = {"size": size, "hash": hash}
    client_url = settings['client']['library']['url']
    data['identity'] = get_settings()['client']['library']['identity']
    url = "%s/startPublish" % client_url
    response = requests.post(url, data=data)
    
    code = response.status_code
    if code != 200:
        msg = response.error
        raise Exception("Library Server Error: (%s) %s" % (code, msg))

    url = upload_engine.upload(filename, size, hash, response.json)
    return url

def complete_publish(settings, size, hash, url, metadata):
    if size and hash:
        # local file
        metadata.update({"hash": hash, "size": size})
    else:
        # url
        metadata.update({"url": url})

    client_url = settings['client']['library']['url']
    metadata['identity'] = settings['client']['library']['identity']
    response = requests.post("%s/completePublish" % client_url, data=metadata)

def configure():
    pass