import requests

from django.db import models
from library import Library

class Connection(models.Model):
    """
    Represents a set of files that get shared between two libraries.
    """
    identity = models.CharField(max_length=256) # full identity of connecting library (username@domain).
    #filter_query = PickledObjectField() # the query object that defines the files
    my_auth_token = models.CharField(max_length=32) # whoever is in possession of this token can access this connection
    their_auth_token = models.CharField(max_length=32)
    date_created = models.DateTimeField()
    pending = models.BooleanField(default=False)
    pending_message = models.TextField()
    #pending_query = PickledObjectField()
    
    def __unicode__(self):
        mode = 'follow' if not self.my_auth_token else 'auth'
        return "%s -> %s [%s]" % (self.library.identity, self.identity, mode)

    @classmethod
    def create_pending_connection(cls, library, identity, their_auth_token, query, message):
        """
        Create a 'pending' connection object for when other people request authorization.
        Its becomes non-pending when the owner of the library accepts the authorization.
        """
        return cls.objects.create(
            library=library,
            identity=identity,
            #filter_query='',
            my_auth_token='',
            their_auth_token=their_auth_token,
            date_created=datetime.datetime.now(),
            pending=True,
            pending_message=message,
            #pending_query=query,
        )

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
            response = requests.post(
                "https://%s/api/requestAuthorization.json" % domain,
                data={
                    'target_identity': identity,
                    'requesting_identity': library.identity,
                    'requesting_token': my_auth_token,
                    'request_message': request_message,
                    'request_query': request_query or '',
                },
                verify=(not get_config('debug')),
            )
            if response.status_code != 200 or response.json() != "OK":
                raise InvalidData("Identity not valid")

        return cls.objects.create(
            library=library,
            identity=identity,
            filter_query=filter_query,
            my_auth_token=my_auth_token,
            their_auth_token='',
            date_created=datetime.datetime.now(),
            pending=False,
        )
