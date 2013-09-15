import os
from dropbox import client
from models import get_dropbox_session

import logging

def upload(filename, endfilename, access_token):
    logging.info('Commencing upload to Dropbox')
    print("Upload to Dropbox")
    
    sess = get_dropbox_session(
        token_key=access_token['key'],
        token_secret=access_token['secret'],
    )

    db = client.DropboxClient(sess)

    with open(filename) as f:
        remote_path = os.path.join('Library', endfilename)
        response = db.put_file(remote_path, f)

    return db.share(response['path'])['url']