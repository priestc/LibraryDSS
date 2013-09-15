import base64

from django.db import models
from library import Library

class StorageEngine(models.Model):
    library = models.ForeignKey(Library)
    name = models.CharField(max_length=128)
    retired = models.BooleanField()
    connection_data = models.TextField()

    def __init__(self, *args, **kwargs):
        """
        Turn the connection_data arg into json. You must pass in only serializable
        data. Also, automatically pickle and b64encode google credentials objects.
        """
        # retired default is False
        kwargs['retired'] = False if not 'retired' in kwargs else kwargs['retired']
        super(StorageEngine, self).__init__(*args, **kwargs)

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
        items = session.query(Item).filter_by(storage_engine_id=self.id).all()
        return human(sum(x.size for x in items))

    def get_total_items(self):
        """
        Return total number of items stored onto this storage engine.
        """
        session = get_config('db_session')
        return session.query(Item).filter_by(storage_engine_id=self.id).count()

    def sign_aws_policy(self, policy_document):
        AWS_SECRET_ACCESS_KEY = self.connection_data['aws_secret']
        if not AWS_SECRET_ACCESS_KEY:
            raise Exception("Can not generate policy and signature")
        policy = base64.b64encode(policy_document)
        signature = base64.b64encode(hmac.new(AWS_SECRET_ACCESS_KEY, policy, hashlib.sha1).digest())
        return policy, signature