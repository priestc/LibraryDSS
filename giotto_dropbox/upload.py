import os
from dropbox import client
from giotto_dropbox.models import get_dropbox_session

import logging
logger = logging.getLogger('dropbox.upload')

def upload(filename, endfilename, access_token):
    logger.info('Commencing upload to Dropbox')
    print "Upload to Dropbox"
    sess = get_dropbox_session(
        token_key=access_token['key'],
        token_secret=access_token['secret'],
    )

    c = client.DropboxClient(sess)

    with open(filename) as f:
        remote_path = os.path.join('Library', endfilename)
        response = c.put_file(remote_path, f)

    import debug

    return response['path']