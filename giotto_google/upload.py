import mimetypes
import httplib2

from apiclient import errors
from apiclient.http import MediaFileUpload
from apiclient.discovery import build

def upload(filename, endfilename, credentials):
    """
    Upload to googe drive. Called by either front end or back end.
    """
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
        file = service.files().insert(
            body=body,
            media_body=media_body).execute()

        # Uncomment the following line to print the File ID
        # print 'File ID: %s' % file['id']

        return file
    except errors.HttpError, error:
        print 'An error occured: %s' % error
        return None