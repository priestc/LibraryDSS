import httplib2

from models import Library, StorageEngine, Item, MetaData, Connection
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

def execute_query(query):
    return "foo"

def show_connections(user=LOGGED_IN_USER):
    library = Library.get(username=user.username)
    return {
        'site_domain': get_config('domain'),
        'username': user.username,
        'existing_connections': library.connections
    }

def connection_submit(identity, request_auth=False, user=LOGGED_IN_USER, filter_query=None, request_query=None, request_message=None):
    library = Library.get(username=user.username)
    library.connection_details(identity, filter_query, request_query, request_message, pending=False)

def request_authorization(target_identity, requesting_identity, requesting_token, request_message, request_query):
    """
    Called by other people who wish to connect with me.
    """
    library = library.get(identity=target_identity)
    library.connection_details()

def home(user=LOGGED_IN_USER):
    session = get_config('db_session')
    library_count = session.query(Library).count()
    item_count = session.query(Item).count() or 0
    total_size = 0 #session.query(func.sum(Item.size))[0][0] or 0
    return {
        'user': user,
        'library_count': library_count,
        'item_count': item_count,
        'total_size': sizeof_fmt(total_size)
    }

def dashboard(user=LOGGED_IN_USER):
    session = get_config('db_session')
    identity = "%s@%s" % (user.username, get_config('domain'))
    conns = session.query(Connection)\
                   .filter(Library.identity==identity)\
                   .order_by(Connection.date_created.desc())
    pubs = session.query(Item)\
                  .filter(Library.identity==identity)\
                  .order_by(Item.date_published.desc())
    return {
        'latest_connections': conns,
        'latest_publications': pubs,
    }

def start_publish(size, hash, username=USER):
    """
    Based on the size and hash, determine which storage engine should get this
    new upload.
    """
    library = Library.get(username=username)
    return library.get_storage(size)

def finish_publish(hash, metadata, engine_id=None, username=USER):
    """
    After the client's upload is complete, this api is hit to actually
    finish the publish process.
    """
    identity = "%s@%s" % (username, get_config('domain'))
    library = Library.get(identity=identity)
    library.add_item(
        engine_id=engine_id,
        origin=identity,
        metadata=metadata
    )
    return "OK"

def items(query=None, user=LOGGED_IN_USER, username=USER):
    """
    Given an LQL query and a library identity, return the items that match.
    """
    # in the case of an authenticated request through the browser;
    # no 'identity' will be sent, so just go by username.
    identity = "%s@%s" % (user.username or username, get_config('domain'))

    if not identity:
        raise NotAuthorized()

    library = Library.get(identity=identity)
    session = get_config('db_session')
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
        'keys': library.all_keys(),
    }

def engine_dashboard(user=LOGGED_IN_USER):
    library = Library.get(username=user.username)
    names = [x.name for x in library.engines]
    
    google_drive_url = None
    if 'googledrive' not in names:
        # only generate a google drive auth url if no google drive engine exists
        google_drive_url = get_google_flow('https').step1_get_authorize_url()

    dropbox_url = None
    if 'dropbox' not in names:
        dropbox_url = get_dropbox_authorize_url(user, callback_scheme='https')

    return {
        'identity': user.username,
        'google_drive_url': google_drive_url,
        'engines': library.engines,
        'dropbox_url': dropbox_url,
    }

def edit_item(size, hash, user=LOGGED_IN_USER):
    item = Item.get(size=size, hash=hash, user=user)
    return item

def backup(username=USER):
    library = Library.get(username=username)
    return library.items

def update_engine(engine_id, data=ALL_DATA, user=LOGGED_IN_USER):
    session = get_config('db_session')
    engine = session.query(StorageEngine, Library)\
                    .filter(StorageEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    return {'e': engine}

def migrate_off_engine(engine_id, user=LOGGED_IN_USER):
    session = get_config('db_session')
    engine = session.query(StorageEngine, Library)\
                    .filter(StorageEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    engine.migrate_off()
    return Redirection('/settings')

def migrate_onto_engine(engine_id, user=LOGGED_IN_USER):
    session = get_config('db_session')
    engine = session.query(StorageEngine, Library)\
                    .filter(StorageEngine.id==engine_id)\
                    .filter(Library.identity==user.username).first()
    engine.migrate_onto()
    return Redirection('/settings')

def autocomplete(dimension, value):
    if dimension == 'key':
        return MetaData.all_values_for_key(value)

    raise InvalidInput("Ivalid dimension")
