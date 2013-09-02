import datetime
import base64
import pickle
import json
import hashlib
import random
import os

from giotto import get_config

Base = get_config('Base')

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, func, desc, PickleType
from sqlalchemy.orm import relationship
from giotto.primitives import LOGGED_IN_USER
from giotto.exceptions import DataNotFound
from giotto.utils import random_string

from utils import fuzzy_to_datetime, datetime_to_fuzzy, sizeof_fmt, is_date_key
from LQL import Query

IMMUTABLE_BUILT_IN = ['origin', 'license']

class Connection(Base):
    """
    Represents a set of files that get shared between two libraries.
    """
    id = Column(Integer, primary_key=True)
    library_id = Column(ForeignKey("giotto_library.identity"))
    library = relationship('Library', backref="connections")
    identity = Column(String) # full identity of connecting library (username@domain).
    filter_query = Column(PickleType) # the query object that defines the files
    my_auth_token = Column(String(32)) # whoever is in possession of this token can access this connection
    their_auth_token = Column(String(32))
    date_created = Column(DateTime)
    
    def __repr__(self):
        mode = 'follow' if not self.my_auth_token else 'auth'
        return "%s -> %s [%s]" % (self.library.identity, self.identity, mode)

    @classmethod
    def create_connection(cls, library, identity, request_auth=False, filter_query=None, request_query=None, request_message=None):
        """
        The owner of `library` wants to connect to `identity` with `filter_query` applied
        to all data coming back from said connection.
        """
        username, domain = identity.split('@') # of the person who we want to connect to
        if not request_auth:
            my_auth_token = ''
            their_auth_token = ''
        else:
            my_auth_token = random_string(32)
            response = requests.get(
                "https://%s/api/requestAuthorizedConnection" % domain,
                data={
                    'target_identity': identity,
                    'requesting_identity': library.identity,
                    'requesting_token': my_auth_token,
                    'request_message': request_message,
                    'request_query': request_query,
                }
            )
            their_auth_token = response.json()['auth_token']

        conn =cls(
            library=library,
            identity=identity,
            filter_query=filter_query,
            my_auth_token=my_auth_token,
            their_auth_token=their_auth_token,
            date_created=datetime.datetime.now(),
        )

        session = get_config('db_session')
        session.add(conn)
        session.commit()
        return conn

class Library(Base):
    identity = Column(String, primary_key=True)
    password = Column(String)
    items = relationship('Item', primaryjoin="Library.identity==Item.library_identity", backref="library")

    def __repr__(self):
        return "%s (%s)" % (self.identity, len(self.items))

    def all_values_for_key(self, user, key):
        q = session.query(MetaData.value).filter(key=key)
        return q.all()

    def connection_details(self, identity, request_auth=False, filter_query=None, request_query=None, request_message=None):
        """
        Update details of a connection
        """
        session = get_config('db_session')
        # try to find existing connection.
        conn = session.query(Connection).filter(Library.identity==identity, Connection.identity==identity).first()
        if not conn:
            Connection.create_connection(
                library=self,
                identity=identity,
                request_auth=request_auth,
                filter_query=filter_query,
                request_query=request_query,
                request_message=request_message,
            )
        else:
            conn.filter_query = filter_query
            session.add(conn)
            session.commit()

    @classmethod
    def get(cls, identity=None, username=None):
        """
        Get Library by identity.
        """
        if not identity:
            identity = "%s@%s" % (username, get_config('domain'))
        session = get_config('db_session')
        return session.query(cls).get(identity)

    def has(self, size=None, hash=None):
        """
        Does this size/hash pair exist in my library?
        """
        session = get_config('db_session')
        items = session.query(MetaData, Library)\
            .filter(Library.identity == self.identity)\
            .filter(
                (MetaData.key == 'size' and MetaData.value == size) and 
                (MetaData.key == 'hash' and MetaData.value == hash)
            )

        return len(items.all()) > 0

    def all_keys(self):
        """
        Return a list of all keys that are used in describing the library items
        in this library. FIXME: have this be one db query.
        """
        keys = set()
        for item in self.items:
            k = set(item.keys())
            keys = keys.union(k)

        return keys

    def get_storage(self, size):
        x = self.engines
        random.shuffle(x)
        return x

    def add_storage(self, engine, connection_data):
        e = UploadEngine(library=self, name=engine, connection_data=connection_data)
        session = get_config('db_session')
        session.add(e)
        session.commit()
        return e

    def execute_query(self, query, identity=None):
        """
        Pass in a string LQL query, nd out comes all matching items for that
        query.
        """
        items = session.query(Item).join(MetaData).filter(Item.library==self)
        all_items = Query(as_string=query).execute(self)

    def add_item(self, engine_id, metadata, origin):
        """
        Import a new item into the Library.
        """
        session = get_config('db_session')
        metadata = json.loads(metadata)
        i = Item(
            engine_id=engine_id,
            library=self,
            origin=origin,
            date_published=datetime.datetime.now(),
        )

        metadata['date_published'] = datetime.datetime.now().isoformat()

        i.reset_metadata(metadata)
        session.add(i)
        session.commit()

class Item(Base):
    id = Column(Integer, primary_key=True)
    library_identity = Column(ForeignKey("giotto_library.identity"))
    origin = Column(String, nullable=False)
    storage_engine_id = Column(ForeignKey("giotto_uploadengine.id"))
    storage_engine = relationship('StorageEngine')
    date_published = Column(DateTime)

    def human_size(self):
        return sizeof_fmt(self.size)

    @property
    def size(self):
        return int(self.get_metadata('size'))

    @classmethod
    def get(cls, id, user=LOGGED_IN_USER):
        session = get_config('db_session')
        ret = session.query(cls)\
                      .filter_by(id=id)\
                      .filter_by(library_identity=user.username)\
                      .first()

        if not ret:
            raise DataNotFound()

        return ret

    def __repr__(self):
        return "[%s]" % (self.get_metadata('title')) #, self.hash, self.mimetype)

    def get_icon(self):
        """
        Based on the mimetype and some other verious metadata, return an icon
        that represents this item. Used in the UI.
        """
        mt = self.get_metadata('mimetype')

        if mt.startswith("image/"):
            return "image"

        if mt.startswith("video/"):
            return "video"

        if mt.startswith("text/"):
            return "text"

        return "unknown"


    def reset_metadata(self, metadata):
        session = get_config('db_session')
        session.query(MetaData).filter_by(item=self).delete()
        for key, value in metadata.items():
            m = MetaData(key=key, value=value, item=self)
            session.add(m)
        session.commit()

    
    def get_metadata(self, key):
        """
        Get metadata for this
        """
        session = get_config('db_session')
        result = session.query(MetaData).filter_by(item=self, key=key).first()
        return (result and result.value) or ''

    def get_all_metadata(self, only_mutable=False):
        """
        Return all metadata for this item. Sorted by key name alphabetical.
        mutable: only include fields that can be changed
        """
        session = get_config('db_session')
        query = session.query(MetaData).filter_by(item=self).order_by(MetaData.key)
        meta = {m.key: m.get_value() for m in query}
        
        if not only_mutable:
            fields = IMMUTABLE_BUILT_IN

        meta.update({key: self.get_metadata(key) for key in fields})
        return sorted([(key, value) for key, value in meta.items()], key=lambda x: x[0])

    def keys(self):
        """
        return all keys that exist to describe this item
        """
        return [x[0] for x in self.get_all_metadata()]

    def todict(self):
        return self.get_all_metadata()

class MetaData(Base):
    id = Column(Integer, primary_key=True)
    key = Column(String)
    value = Column(String)
    date_value = Column(DateTime, nullable=True)
    
    item_id = Column(ForeignKey("giotto_item.id"))
    item = relationship('Item', primaryjoin="Item.id==MetaData.item_id", backref="metadata")

    def __repr__(self):
        return "[id=%s] %s=%s" % (self.item.hash[:5]+ '...', self.key, self.value)

    def __init__(self, **kwargs):
        if is_date_key(kwargs['key']):
            kwargs['date_value'] = fuzzy_to_datetime(kwargs['value'])
        return super(MetaData, self).__init__(**kwargs)

    def get_value(self):
        if is_date_key(self.key):
            return self.date_value
        return self.value

class UploadEngine(Base):
    id = Column(Integer, primary_key=True)
    library_identity = Column(ForeignKey("giotto_library.identity"))
    library = relationship("Library", backref="engines")
    name = Column(String, nullable=False)
    retired = Column(Boolean)
    connection_data = Column(PickleType)

    def __init__(self, *args, **kwargs):
        """
        Turn the connection_data arg into json. You must pass in only serializable
        data. Also, automatically pickle and b64encode google credentials objects.
        """
        # retired default is False
        kwargs['retired'] = False if not 'retired' in kwargs else kwargs['retired']
        super(UploadEngine, self).__init__(*args, **kwargs)

    def todict(self):
        cd = base64.b64encode(pickle.dumps(self.connection_data))
        return {'name': self.name, 'data': cd, 'id': self.id}

    def __repr__(self):
        return "Engine: %s %s" % (self.name, self.library_identity)

    def get_other_engines(self):
        return []

    def migrate_off(self):
        """
        Move all files off of this engine and onto other engines.
        """

    def migrate_onto(self):
        """
        Move all data from other engines onto this engine.
        """

    def get_total_size(self, human=False):
        """
        The total bytes of all files stored in this engine. Does not call the
        engine API, just goes by the local database.
        human == return as human readable with 'MB', 'KB', etc.
        """
        session = get_config('db_session')
        human = sizeof_fmt if human else lambda x: x
        items = session.query(Item).filter_by(engine_id=self.id).all()
        return human(sum(x.size for x in items))

    def get_total_items(self):
        """
        Return total number of items stored onto this storage engine.
        """
        session = get_config('db_session')
        return session.query(Item).filter_by(engine_id=self.id).count()

def configure():
    """
    For changing configuration for the server.
    """
    return