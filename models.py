import datetime
import base64
import pickle
import json
import hashlib
import random
import os

from giotto import get_config

Base = get_config('Base')
session = get_config('db_session')

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, func, desc, PickleType
from sqlalchemy.orm import relationship
from giotto.primitives import LOGGED_IN_USER
from giotto.exceptions import DataNotFound

from utils import fuzzy_to_datetime, datetime_to_fuzzy, sizeof_fmt, is_date_key
from LQL import Query

IMMUTABLE_BUILT_IN = ['origin', 'license']

class Contract(Base):
    """
    Represents a set of files that get shared between two libraries.
    """
    id = Column(Integer, primary_key=True)
    library_id = Column(ForeignKey("giotto_library.identity"))
    library = relationship('Library', backref="disributions")
    identities = Column(String) # people these files are shared with
    query = Column(PickleType) # the query object that defines the files
    license = Column(String) # the license that gets applied to the files when moved.

class Library(Base):
    identity = Column(String, primary_key=True)
    password = Column(String)
    items = relationship('Item', primaryjoin="Library.identity==Item.library_identity", backref="library")

    def __repr__(self):
        return "%s (%s)" % (self.identity, len(self.items))

    def all_values_for_key(self, user, key):
        q = session.query(MetaData.value).filter(key=key)
        return q.all()

    @classmethod
    def get(cls, identity):
        """
        Get Library by identity.
        """
        return session.query(cls).get(identity)

    def has(self, size=None, hash=None):
        """
        Does this size/hash pair exist in my library?
        """
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
        metadata = json.loads(metadata)
        i = Item(
            engine_id=engine_id,
            library=self,
            origin=origin,
        )

        metadata['date_published'] = datetime.datetime.now().isoformat()

        i.reset_metadata(metadata)
        session.add(i)
        session.commit()

class Item(Base):
    id = Column(Integer, primary_key=True)
    library_identity = Column(ForeignKey("giotto_library.identity"))
    origin = Column(String, nullable=False)
    engine_id = Column(ForeignKey("giotto_uploadengine.id"))
    engine = relationship('UploadEngine')

    def human_size(self):
        return sizeof_fmt(self.size)

    @property
    def size(self):
        return int(self.get_metadata('size'))

    @classmethod
    def get(cls, id, user=LOGGED_IN_USER):
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
        session.query(MetaData).filter_by(item=self).delete()
        for key, value in metadata.items():
            m = MetaData(key=key, value=value, item=self)
            session.add(m)
        session.commit()

    
    def get_metadata(self, key):
        """
        Get metadata for this
        """
        result = session.query(MetaData).filter_by(item=self, key=key).first()
        return (result and result.value) or ''

    def get_all_metadata(self, only_mutable=False):
        """
        Return all metadata for this item. Sorted by key name alphabetical.
        mutable: only include fields that can be changed
        """
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
        human = sizeof_fmt if human else lambda x: x
        items = session.query(Item).filter_by(engine_id=self.id).all()
        return human(sum(x.size for x in items))

    def get_total_items(self):
        """
        Return total number of items stored onto this storage engine.
        """
        return session.query(Item).filter_by(engine_id=self.id).count()

def configure():
    """
    For changing configuration for the server.
    """
    return