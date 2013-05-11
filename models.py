import datetime
import base64
import pickle
import json
import hashlib
import random
import os

from giotto import get_config

Base = get_config('Base')
session = get_config('session')

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, func, desc, PickleType
from sqlalchemy.orm import relationship
from giotto.primitives import LOGGED_IN_USER
from giotto.exceptions import DataNotFound

from utils import fuzzy_to_datetime, datetime_to_fuzzy, sizeof_fmt, is_date_key
from query import execute_query

IMMUTABLE_BUILT_IN = ['hash', 'size', 'date_published', 'license', 'origin']
MUTABLE_BUILT_IN = ['mimetype', 'date_created', 'url']
BUILT_IN = IMMUTABLE_BUILT_IN + MUTABLE_BUILT_IN

class Distribution(Base):
    """
    Represents a set of files that get shared between two parties.
    """
    id = Column(Integer, primary_key=True)
    library_id = Column(ForeignKey("giotto_library.identity"))
    library = relationship('Library', backref="disributions")
    identities = Column(String) # people these files are shared with
    query = Column(String) # the query that defines the files
    license = Column(String) # the license that gets applied to the files when moved.

class Library(Base):
    identity = Column(String, primary_key=True)
    password = Column(String)
    items = relationship('Item', primaryjoin="Library.identity==Item.library_identity", backref="library")

    def __repr__(self):
        return "%s (%s)" % (self.identity, len(self.items))

    @classmethod
    def get(cls, identity):
        """
        Get Library by identity.
        """
        return session.query(cls).get(identity)

    def has(self, size=None, hash=None):
        """
        Does this size/md5 pair exist in my library?
        """
        items = session.query(Item).filter_by(library=self).filter_by(size=size, hash=hash)
        return len(items.all()) > 0

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
        items = session.query(Item).join(MetaData).filter(Item.library==self)
        return execute_query(items, query)

    def add_item(self, engine_id, date_created, url, size, hash, mimetype, metadata, license='restricted'):
        """
        Import a new item into the Library.
        """
        i = Item(
            engine_id=engine_id,
            url=url,
            library=self,
            size=size,
            origin=self.identity,
            mimetype=mimetype,
            license=license,
            date_published=datetime.datetime.now(),
            date_created=fuzzy_to_datetime(date_created),
            hash=hash,
        )
        i.reset_metadata(metadata)
        session.add(i)
        session.commit()

class Item(Base):
    library_identity = Column(ForeignKey("giotto_library.identity"))
    size = Column(Integer, nullable=False)
    hash = Column(String(64), primary_key=True)
    date_published = Column(DateTime, nullable=False)
    date_created = Column(DateTime, nullable=False)
    mimetype = Column(String, nullable=False)
    url = Column(String, nullable=False)
    license = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    engine_id = Column(ForeignKey("giotto_uploadengine.id"))
    engine = relationship('UploadEngine')

    def human_size(self):
        return sizeof_fmt(self.size)

    @classmethod
    def get(cls, size, hash, user=LOGGED_IN_USER):
        ret = session.query(cls)\
                      .filter_by(size=size, hash=hash)\
                      .filter_by(library_identity=user.username)\
                      .first()

        if not ret:
            raise DataNotFound()

        return ret

    def __repr__(self):
        return "[%s]" % (self.date_created) #, self.hash, self.mimetype)

    def reset_metadata(self, metadata):
        session.query(MetaData).filter_by(item=self).delete()
        for key, value in metadata.items():
            if key in BUILT_IN:
                setattr(self, key, value)
            else:
                m = MetaData(key=key, value=value, item=self)
                session.add(m)
        session.commit()

    
    def get_metadata(self, key):
        """
        Get metadata for this
        """
        if key in BUILT_IN:
            ret = getattr(self, key)
            if key.startswith("date_"):
                return datetime_to_fuzzy(ret)
            return ret

        result = session.query(MetaData).filter_by(item=self, key=key).first()
        return (result and result.value) or ''

    def get_all_metadata(self, only_mutable=False):
        """
        Return all metadata for this item. Sorted by key name alphabetical.
        mutable: only include fields that can be changed
        """
        query = session.query(MetaData).filter_by(item=self).order_by(MetaData.key)
        meta = {m.key: m.get_value() for m in query}
        
        fields = MUTABLE_BUILT_IN
        if not only_mutable:
            fields += IMMUTABLE_BUILT_IN

        meta.update({
            key: self.get_metadata(key) for key in fields
        })

        return sorted([(key, value) for key, value in meta.items()], key=lambda x: x[0])

    def as_json(self):
        data = {"origin": self.origin, "hash": self.hash, "size": self.size}
        data.update(self.get_metadata())
        return json.dumps(data)

class MetaData(Base):
    id = Column(Integer, primary_key=True)
    key = Column(String)
    value = Column(String)
    item_id = Column(ForeignKey("giotto_item.hash"))
    item = relationship('Item', primaryjoin="Item.hash==MetaData.item_id", backref="metadata")

    def __repr__(self):
        return "%s %s=%s" % (self.item, self.key, self.value)

    def __init__(self, **kwargs):
        if is_date_key(kwargs['key']):
            kwargs['value'] = fuzzy_to_datetime(kwargs['value'])
        return super(MetaData, self).__init__(**kwargs)

    def get_value(self):
        if is_date_key(self.key):
            return datetime_to_fuzzy(self.value)
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