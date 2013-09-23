from giotto import get_config
from library import Library
from storage_engines import StorageEngine
from googledrive.models import get_google_flow

def dropbox_api_callback(user, access_token):
    """
    Handles the request that the user makes given by the dropbox API as part of
    the oauth process. This is the callback used in oauth1.
    """
    library = Library.objects.get(username=user.username)
    at = {'key': access_token.key, 'secret': access_token.secret}
    engine = StorageEngine.objects.create(
        name="dropbox",
        connection_data=at,
        library=library
    )

    return "/manage/%s" % user.username

def google_api_callback(user, credentials):
    """
    After authenticating with the Google API Auth server, google redirects the user
    back to this program, where `code` is exchanged for an auth token, and
    then stored. This auth token is what subsiquent API calls will have to include.
    """
    library = Library.objects.get(username=user.username)
    engine = StorageEngine.objects.create(
        name="googledrive",
        connection_data=credentials,
        library=library
    )

    return '/manage/%s' % user.username