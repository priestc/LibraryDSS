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

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, func, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import ConcreteBase

from utils import fuzzy_to_datetime, sizeof_fmt
from query import compile_query

BUILT_IN_ITEM_ATTRS = ['mimetype', 'size', 'date_published', 'date_created', 'license', 'origin']

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
        return random.choice(self.engines)

    def add_storage(self, engine, connection_data):
        if engine == 'googledrive':
            e = UploadEngine(library=self, name=engine, google_credentials=connection_data)
        else:
            e = UploadEngine(library=self, name=engine, _connection_data=connection_data)
        session.add(e)
        session.commit()
        return e

    def execute_query(self, query):
        query_obj = compile_query(query)
        #import debug
        #print query_obj

        # all metadata pairs for all items in this library.
        items = session.query(Item).join(MetaData).filter(Item.library==self)

        for k, (v, method) in query_obj.items():
            attr = k

            is_date = (k.endswith('_date') or k.startswith('date_') or '_date_' in k)
            if is_date and v != '*':
                # this value will be interpreted as a date.
                v = fuzzy_to_datetime(v)

            if attr in BUILT_IN_ITEM_ATTRS:
                # attributes that are stored directly onto the model.
                if attr == 'mimetype' and v.endswith('*'):
                    # wildcard mimetype querying
                    first_part = v[:-1]
                    items = items.filter(Item.mimetype.startswith(first_part))
                elif attr == 'mimetype':
                    # exact mimetype querying
                    items = items.filter(getattr(Item, k)==v)
                elif is_date:
                    if method == 'less':
                        items = items.filter(getattr(Item, attr)<v)
                    elif method == 'greater':
                        items = items.filter(getattr(Item, attr)>=v)
                    else:
                        # TODO: full fuzzy matching
                        items = items.filter(getattr(Item, attr)==v)
                else:
                    items = items.filter(getattr(Item, attr)==v)

            else:
                # attributes that are stored on the MetaData table.
                if v == '*':
                    items = items.filter(MetaData.key==k)
                else:
                    items = items.filter(MetaData.key==k, MetaData.value==v)

        #print "after: ", items.all()
        return items.all()

    def add_item(self, engine, date_created, url, size, hash, mimetype, metadata, license='restricted'):
        """
        Import a new item into the Library.
        """
        i = Item(
            engine=engine,
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
        i.set_metadata(metadata)
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

    def __repr__(self):
        return "[%s]" % (self.date_created) #, self.hash, self.mimetype)

    def set_metadata(self, metadata):
        for k, v in metadata.items():
            if k.startswith('date'):
                v = fuzzy_to_datetime(v)
            m = MetaData(key=k, value=v, item=self)
            session.add(m)
        session.commit()

    def metadata_to_dict(self):
        meta = session.query(MetaData).filter_by(library=self)
        return {m.key: m.value for m in meta}
        
    def as_json(self):
        data = {"origin": self.origin, "hash": self.hash, "filesize": self.filesize}
        data.update(self.metadata_to_dict)
        return json.dumps(data)

class MetaData(Base):
    id = Column(Integer, primary_key=True)
    key = Column(String)
    value = Column(String)
    item_id = Column(ForeignKey("giotto_item.hash"))
    item = relationship('Item', primaryjoin="Item.hash==MetaData.item_id", backref="metadata")

    def __repr__(self):
        return "%s %s=%s" % (self.item, self.key, self.value)

class UploadEngine(Base):
    id = Column(Integer, primary_key=True)
    library_identity = Column(ForeignKey("giotto_library.identity"))
    library = relationship("Library", backref="engines")
    name = Column(String, nullable=False)
    retired = Column(Boolean)
    _connection_data = Column(String) # json encoded

    def __init__(self, *args, **kwargs):
        """
        Turn the connection_data arg into json. You must pass in only serializable
        data. Also, automatically pickle and b64encode google credentials objects.
        """
        gc = kwargs.pop('google_credentials', None)
        if gc:
            encoded = {'credentials': base64.b64encode(pickle.dumps(gc))}
            kwargs['_connection_data'] = json.dumps(encoded)
        else:
            kwargs['_connection_data'] = json.dumps(kwargs['_connection_data'])

        kwargs['retired'] = False if not 'retired' in kwargs else kwargs['retired']

        super(UploadEngine, self).__init__(*args, **kwargs)

    @property
    def connection_data(self):
        if getattr(self, "__connection_data", False):
            return self.__connection_data

        self.__connection_data = json.loads(self._connection_data)

        if self.name == 'googledrive':
            credentials = self.__connection_data['credentials']
            unencoded = pickle.loads(base64.b64decode(credentials))
            self.__connection_data['credentials'] = unencoded

        return self.__connection_data

    def todict(self):
        connection_data = self._connection_data()
        return {'name': self.name, 'data': connection_data}

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