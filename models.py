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

from utils import fuzzy_to_datetime

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
            e = UploadEngine(library=self, name=engine, connection_data=connection_data)
        session.add(e)
        session.commit()
        return e

    def execute_query(self, **query):
        # all metadata pairs for all items in this library.
        items = session.query(Item).join(MetaData).filter(Item.library==self)

        for k, v in query.items():
            if ' ' not in k:
                items = items.filter(MetaData.key==k, MetaData.value==v)
            else:
                raise NotImplementedError("Fancy querying not supported yet")

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
        return "[%i#%s %s]" % (self.size, self.hash, self.mimetype)

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
    connection_data = Column(String) # json encoded

    def todict(self):
        connection_data = json.loads(self.connection_data)

        if self.name == 'googledrive':
            credentials = connection_data['credentials']
            unencoded = pickle.loads(base64.b64decode(credentials))
            connection_data['credentials'] = unencoded

        return {'name': self.name, 'data': connection_data}

    def __repr__(self):
        return "Engine: %s %s" % (self.name, self.library_identity)

    def get_total_size(self):
        """
        The total bytes of all files stored in this engine. Does not call the
        engine API, just goes by the local database.
        """
        items = session.query(Item).filter_by(engine_id=self.id).all()
        return sum(x.size for x in items)

    def __init__(self, *args, **kwargs):
        """
        Turn the connection_data arg into json. You must pass in only serializable
        data. Also, automatically pickle and b64encode google credentials objects.
        """
        gc = kwargs.pop('google_credentials', None)
        if gc:
            encoded = {'credentials': base64.b64encode(pickle.dumps(gc))}
            kwargs['connection_data'] = json.dumps(encoded)
        else:
            kwargs['connection_data'] = json.dumps(kwargs['connection_data'])

        super(UploadEngine, self).__init__(*args, **kwargs)

def configure():
    """
    For changing configuration for the server.
    """
    return