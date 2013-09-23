import httplib2

from library import Library, Item, MetaData
from storage_engines import StorageEngine
from connections import Connection

from giotto.primitives import ALL_DATA, USER, LOGGED_IN_USER
from giotto.exceptions import NotAuthorized
from giotto.utils import jsonify
from giotto import get_config

from apiclient.discovery import build
from googledrive.models import get_google_flow
from gio_dropbox.models import get_dropbox_authorize_url
from aws import get_bucket_name
from giotto.control import Redirection
from utils import sizeof_fmt

def addS3(secret_key, access_token, user=LOGGED_IN_USER):
    bucket_name = get_bucket_name(user.username, get_config('domain'), access_token, secret_key)
    library = Library.objects.get(username=user.username)
    library.add_storage('s3', {
        'aws_key': access_token,
        'aws_secret': secret_key,
        'bucket_name': bucket_name
        }
    )

def execute_query(query):
    return "foo"

def show_connections(user=LOGGED_IN_USER):
    conns = Connection.objects.all()
    return {
        'site_domain': get_config('domain'),
        'username': user.username,
        'existing_connections': [x for x in conns if not x.pending],
        'pending_connections': [x for x in conns if x.pending]
    }

def connection_submit(identity, request_auth=False, user=LOGGED_IN_USER, filter_query=None, request_query=None, request_message=None):
    library = Library.objects.get(username=user.username)
    library.connection_details(
        identity=identity,
        filter_query=filter_query,
        request_auth=request_auth,
        request_query=request_query,
        request_message=request_message,
    )

def accept_connection_request(connection_id, user=LOGGED_IN_USER):
    connection = Connection.objects.get(id=connection_id)
    connection.pending = False
    connection.save()

def request_authorization(target_identity, requesting_identity, requesting_token, request_message, request_query=None):
    """
    Called by other people who wish to connect with me.
    """
    library = Library.objects.get(identity=target_identity)
    Connection.create_pending_connection(library, requesting_identity, requesting_token, request_message, request_query)
    return "OK"

def home(user=LOGGED_IN_USER):
    library_count = Library.objects.count()
    item_count = Item.objects.count()
    total_size = 0 #session.query(func.sum(Item.size))[0][0] or 0
    return {
        'user': user,
        'library_count': library_count,
        'item_count': item_count,
        'total_size': sizeof_fmt(total_size)
    }

def dashboard(user=LOGGED_IN_USER):
    conns = Connection.objects.order_by("date_created")
    pubs = Item.objects.order_by('date_published')
    return {
        'latest_connections': conns,
        'latest_publications': pubs,
    }

def start_publish(size, hash, username=USER):
    """
    Based on the size and hash, determine which storage engine should get this
    new upload.
    """
    library = Library.objects.get(username=username)
    return library.get_storage(size)

def finish_publish(hash, metadata, engine_id=None, username=USER):
    """
    After the client's upload is complete, this api is hit to actually
    finish the publish process.
    """
    identity = "%s@%s" % (username, get_config('domain'))
    library = Library.objects.get(identity=identity)
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
    library = Library.objects.get()
    items = Item.objects.all()
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
    all_keys = []
    return {
        'parsed_query_json': query_json,
        'library_items': items,
        'items_count': len(items),
        'keys': all_keys,
    }

def engine_dashboard(user=LOGGED_IN_USER):
    names = [x.name for x in StorageEngine.objects.all()]
    
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
        'engines': library.storage_engines,
        'dropbox_url': dropbox_url,
        'has_s3': 's3' in names,
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
