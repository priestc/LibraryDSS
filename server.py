import httplib2

from models import Library, UploadEngine, Item, MetaData
from giotto.primitives import ALL_DATA, USER, LOGGED_IN_USER
from giotto.exceptions import NotAuthorized
from giotto.utils import jsonify
from giotto import get_config

from apiclient.discovery import build
from giotto_google.models import get_google_flow
from giotto_dropbox.models import get_dropbox_authorize_url

from giotto.control import Redirection
from utils import sizeof_fmt

from sqlalchemy import func
session = get_config('session')

def home(user=LOGGED_IN_USER):
    library_count = session.query(Library).count()
    item_count = session.query(Item).count() or 0
    total_size = session.query(func.sum(Item.size))[0][0] or 0
    return {
        'user': user,
        'library_count': library_count,
        'item_count': item_count,
        'total_size': sizeof_fmt(total_size)
    }

def start_publish(size, hash, identity=USER):
    """
    Based on the size and hash, determine which storage engine should get this
    new upload.
    """
    library = Library.get(identity)
    return library.get_storage(size)

def finish_publish(url, size, hash, date_created, mimetype, engine_id=None, metadata=ALL_DATA, identity=USER):
    library = Library.get(identity)
    library.add_item(
        url=url,
        engine_id=engine_id,
        date_created=date_created,
        mimetype=mimetype,
        size=size,
        hash=hash,
        metadata=metadata
    )
    return "OK"

def items(query=None, user=LOGGED_IN_USER, identity=USER):
    """
    Given an LQL query and a library identity, return the items that match.
    """
    if not identity and (user and user.username):
        # in the case of an authenticated request through the browser;
        # no 'identity' will be sent, so just go by username.
        identity = user.username
    
    if not identity:
        raise NotAuthorized()

    library = Library.get(identity)
    items = session.query(Item).join(MetaData).filter(Item.library==library)
    query_json = '[]'

    if query:
        from query import execute_query, parse_query
        parsed = parse_query(query)
        items = execute_query(items, parsed)
        # this json representation of the query that was just used to filter
        # the items will be passed back to the template as a json string
        # so the front end can render the query widget. A string representation
        # is not passed because there is no way to parse LQL in javascript (yet).
        query_json = jsonify(parsed)

    items = items.all()

    return {
        'parsed_query_json': query_json,
        'library_items': items,
        'items_count': len(items),
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

def edit_item(size, hash, user=LOGGED_IN_USER):
    item = Item.get(size=size, hash=hash, user=user)
    return item

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