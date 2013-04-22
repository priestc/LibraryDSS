import httplib2

from models import Library, GoogleDriveEngine
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

def settings(identity):
    library = Library.get(identity)
    s3_engine = library.s3_engine
    googledrive_engine = library.googledrive_engine

    if not googledrive_engine:
        google_drive = get_flow().step1_get_authorize_url()
    else:
        google_drive = library.googledrive_engine

    return {
        'identity': identity,
        'google_drive': google_drive,
        's3_engine': s3_engine,
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

    engine = GoogleDriveEngine(name="drive", credentials=credentials, library=library)
    session = get_config('session')
    session.add(engine)
    session.commit()

    return Redirection('/manage/%s' % user.username)

def backup(identity=USER):
    library = Library.get(identity)
    return library.items
