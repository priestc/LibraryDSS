import httplib2
from apiclient import errors
from apiclient.http import MediaFileUpload

def upload(filename, endfilename, credentials):
    """
    Upload to googe drive. Called by either front end or back end.
    """
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build('drive', 'v2', http=http)
    media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
    body = {
        'title': title,
        'description': "Published by %s" % identity,
        'mimeType': mime_type
    }
    # Set the parent folder.
    if parent_id:
        body['parents'] = [{'id': parent_id}]

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