import datetime
import base64
import pickle
import json
import hashlib
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
        if self.s3_engine:
            return self.s3_engine
        if self.googledrive_engine:
            return self.googledrive_engine

    def add_storage(self, engine, name, details):
        if engine == 's3':
            Engine = S3Engine
        elif engine == 'googledrive':
            Engine = GoogleDriveEngine

        e = Engine(library=self, name=name, **details)
        session.add(e)

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

    def add_item(self, date_created, url, size, hash, mimetype, metadata, license='restricted'):
        """
        Import a new item into the Library.
        """
        i = Item(
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


class S3Engine(Base):
    library_identity = Column(ForeignKey("giotto_library.identity"))
    library = relationship("Library", backref="s3_engine")
    name = Column(String, nullable=False) # TODO: add unique contraint for name + identity
    bucket_name = Column(String, primary_key=True)
    secret_key = Column(String)
    access_key = Column(String)

    def todict(self):
        return {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'bucket_name': self.bucket_name,
            'name': 's3',
        }

    def __repr__(self):
        return "S3: %s" % self.library_identity

class GoogleDriveEngine(Base):
    library_identity = Column(ForeignKey("giotto_library.identity"))
    library = relationship("Library", backref="googledrive_engine")
    name = Column(String, nullable=False) # TODO: add unique contraint for name + identity
    credentials = Column(String, primary_key=True)

    def __init__(self, *a, **kwargs):
        """
        Automatically pickle and b64encode the credentials object.
        """
        kwargs['credentials'] = base64.b64encode(pickle.dumps(kwargs['credentials']))
        super(GoogleDriveEngine, self).__init__(*a, **kwargs)

    def todict(self):
        credentials = pickle.loads(base64.b64decode(self.credentials))
        return {"credentials": credentials, "name": "googledrive"}

    def __repr__(self):
        return "Drive: %s" % self.library_identity


def configure():
    """
    For changing configuration for the server.
    """
    return