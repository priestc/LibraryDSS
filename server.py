import httplib2

from models import Library, UploadEngine, Item
from giotto.primitives import ALL_DATA, USER, LOGGED_IN_USER
from giotto import get_config

from apiclient.discovery import build
from giotto_google.models import get_google_flow
from giotto_dropbox.models import get_dropbox_authorize_url

from giotto.control import Redirection
from utils import sizeof_fmt

from sqlalchemy import func

def home(user=LOGGED_IN_USER):
    session = get_config('session')
    library_count = session.query(Library).count()
    item_count = session.query(Item).count()
    total_size = session.query(func.sum(Item.size))[0][0]
    return {'user': user, 'library_count': library_count, 'item_count': item_count, 'total_size': sizeof_fmt(total_size)}

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

def manage(user=LOGGED_IN_USER):
    """
    Render the library management page.
    """
    library = Library.get(user.username)
    return {
        'library_items': library.items,
    }

def settings(user=LOGGED_IN_USER):
    library = Library.get(user.username)
    names = [x.name for x in library.engines]
    
    google_drive_url = None
    if 'googledrive' not in names:
        # only generate a google drive auth url if no google drive engine exists
        google_drive_url = get_google_flow().step1_get_authorize_url()

    dropbox_url = None
    if 'dropbox' not in names:
        dropbox_url = get_dropbox_authorize_url(user)

    return {
        'identity': user.username,
        'google_drive_url': google_drive_url,
        'engines': library.engines,
        'dropbox_url': dropbox_url,
    }

def backup(identity=USER):
    library = Library.get(identity)
    return library.items

def update_engine(engine_id, data=ALL_DATA, user=LOGGED_IN_USER):
    session = get_config('session')
    engine = session.query(UploadEngine, Library)\
                    .filter(UploadEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    return {'e': engine}

def migrate_off_engine(engine_id, user=LOGGED_IN_USER):
    session = get_config('session')
    engine = session.query(UploadEngine, Library)\
                    .filter(UploadEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    engine.migrate_off()
    return Redirection('/settings')

def migrate_onto_engine(engine_id, user=LOGGED_IN_USER):
    session = get_config('session')
    engine = session.query(UploadEngine, Library)\
                    .filter(UploadEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    engine.migrate_onto()
    return Redirection('/settings')