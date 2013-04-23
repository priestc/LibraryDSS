import httplib2

from models import Library, UploadEngine
from giotto.primitives import ALL_DATA, USER, LOGGED_IN_USER
from giotto import get_config

from apiclient.discovery import build
from google_api import get_flow
from giotto.control import Redirection

def start_publish(size, hash, identity=USER):
    """
    Based on the size and hash, determine which storage engine should get this
    new upload.
    """
    library = Library.get(identity)
    return library.get_storage(size)

def finish_publish(url, size, hash, date_created, mimetype, metadata=ALL_DATA, identity=USER):
    library = Library.get(identity)
    library.add_item(url=url, date_created=date_created, mimetype=mimetype, size=size, hash=hash, metadata=metadata)
    return "OK"

def query(query, identity=USER):
    library = Library.get(identity)
    return library.execute_query(query)

def manage(identity):
    """
    Render the library management page.
    """
    library = Library.get(identity)
    return {
        'library_items': library.items,
    }

def settings(user=LOGGED_IN_USER):
    library = Library.get(user.username)

    google_drive_url = None
    if 'googledrive' not in [x.name for x in library.engines]:
        # only generate a google drive auth url if no google drive engine exists
        google_drive_url = get_flow().step1_get_authorize_url()

    return {
        'identity': user.username,
        'google_drive_url': google_drive_url,
        'engines': library.engines,
    }

def connect_google_api(code, all=ALL_DATA, user=LOGGED_IN_USER):
    """
    After authenticating with the Google API Auth server, it redirects the user
    back to this program, where `code` is exchanged for an auth token, and
    then stored.
    """
    library = Library.get(user.username)
    flow = get_flow()
    credentials = flow.step2_exchange(code)

    engine = UploadEngine(name="googledrive", google_credentials=credentials, library=library)
    session = get_config('session')
    session.add(engine)
    session.commit()

    return Redirection('/manage/%s' % user.username)

def backup(identity=USER):
    library = Library.get(identity)
    return library.items

def update_engine():
    pass

def migrate_off_engine():
    pass

def migrate_onto_engine():
    pass
