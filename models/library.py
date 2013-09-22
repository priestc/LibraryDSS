import datetime
import base64
import pickle
import json
import hashlib
import random
import os
import hmac

import requests

from giotto import get_config

Base = get_config('Base')

from django.db import models
#from picklefield.fields import PickledObjectField
from giotto.primitives import LOGGED_IN_USER
from giotto.exceptions import DataNotFound
from giotto.utils import random_string

from utils import fuzzy_to_datetime, datetime_to_fuzzy, sizeof_fmt, is_date_key
from LQL import Query

IMMUTABLE_BUILT_IN = ['origin', 'date_published']

class Library(object):
    #identity = models.CharField(primary_key=True, max_length=256)

    def __unicode__(self):
        return "%s (%s)" % (self.identity, self.item_set.count())

    def connection_details(self, identity, **kwargs):
        """
        Update details of a connection.
        """
        their_auth_token = kwargs.pop('their_auth_token', None)
        request_auth = kwargs.pop('request_auth', False)
        filter_query = kwargs.pop('filter_query', None)
        request_query = kwargs.pop('request_query', None)
        request_message = kwargs.pop('request_message', None)

        # try to find existing connection.
        conn = Connection.objects.filter(library__identity==self.identity, identity==identity).first()
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
            conn.save()

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

    def get_storage(self, size):
        x = self.engines
        random.shuffle(x)
        return x

    def add_storage(self, engine_name, connection_data):
        e = StorageEngine(library=self, name=engine_name, connection_data=connection_data)
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
        metadata = json.loads(metadata)
        i = Item(
            engine_id=engine_id,
            library=self,
            origin=origin,
            date_published=datetime.datetime.now(),
        )

        metadata['date_published'] = datetime.datetime.now().isoformat()
        i.reset_metadata(metadata)
        i.save()

class Item(models.Model):
    storage_engine = models.ForeignKey('StorageEngine')
    origin = models.CharField(max_length=256, null=False, blank=False)
    date_published = models.DateTimeField()

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

class MetaData(models.Model):
    key = models.TextField(blank=False, null=False)
    string_value = models.TextField(blank=False, null=False)
    date_value = models.DateTimeField()
    num_value = models.FloatField()
    item = models.ForeignKey('Item')

    class Meta:
        app_label = 'dss'

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



