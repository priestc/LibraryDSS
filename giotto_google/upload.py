import mimetypes
import httplib2

from apiclient import errors
from apiclient.http import MediaFileUpload
from apiclient.discovery import build

import logging
logger = logging.getLogger('google_drive.upload')

def upload(filename, endfilename, credentials):
    """
    Upload to googe drive. Called by either front end or back end.
    """
    logger.info('Commencing upload to Google Drive')
    mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build('drive', 'v2', http=http)
    media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
    body = {
        'title': endfilename,
        'description': "Published by me",
        'mimeType': mime_type
    }

    try:
        response = service.files().insert(
            body=body,
            media_body=media_body).execute()
        return response['selfLink'][1]
    except errors.HttpError, error:
        print 'An error occured: %s' % error
        return None