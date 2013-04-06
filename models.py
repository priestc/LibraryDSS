import json
import hashlib
import os

from giotto.primitives import ALL_DATA
from giotto import get_config

Base = get_config('Base')
session = get_config('session')

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, func, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import ConcreteBase

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

    @classmethod
    def query(cls, identity, query):
        library = Library.get(identity)
        return library.execute_query(query)

    @classmethod
    def finish_publish(cls, identity, url, size, hash, metadata=ALL_DATA):
        library = Library.get(identity)
        library.add_item(url, size, hash, metadata)

    def get_storage(self, size):
        if self.s3_engine:
            return self.s3_engine
        if self.googledrive_engine:
            return self.googledrive_engine

    def execute_query(self, query):
        return []

    def add_item(self, url, size, hash, metadata):
        """
        Import a new item into the Library.
        """
        i = Item(url=url, library_identity=self.identity, size=size, hash=hash)
        i.set_metadata(metadata)
        session.add(i)
        session.commit()

class Item(Base):
    library_identity = Column(ForeignKey("giotto_library.identity"))
    size = Column(Integer)
    hash = Column(String, primary_key=True)
    date_published = Column(DateTime)
    date_created = Column(DateTime)
    url = Column(String)
    license = Column(String)
    origin = Column(String)

    @classmethod
    def start_publish(cls, identity, size, hash):
        """
        Based on the size and hash, determine which storage engine should get this
        new upload.
        """
        library = Library.get(identity)
        return library.get_storage(size)

    def __repr__(self):
        return "[%i %s]" % (self.size, self.hash)

    def set_metadata(self, metadata):
        for k, v in metadata.items():
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
    apikey = Column(String, primary_key=True)

    def todict(self):
        return {"apikey": self.apikey, "name": "googledrive"}

    def __repr__(self):
        return "Drive: %s" % self.library_identity


def configure():
    """
    For changing configuration for the server.
    """