from oauth2client.client import flow_from_clientsecrets
from giotto import get_config
from giotto.primitives import ALL_DATA, LOGGED_IN_USER

def get_google_flow(scheme="http"):
    """
    Wrapper for calling `flow_from_clientsecrets` from the google 
    authentication API.
    """
    url = '%s://%s/google/oauth2callback' % (scheme, get_config('domain'))
    return flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/drive',
        redirect_uri=url,
    )

def make_callback_model(callback, scheme='http'):
    def google_api_callback(code=None, all=ALL_DATA, user=LOGGED_IN_USER):
        """
        After authenticating with the Google API Auth server, it redirects the user
        back to this program, where `code` is exchanged for an auth token, and
        then stored.
        """
        if not code:
            raise Exception("No code man")
        flow = get_google_flow(scheme)
        credentials = flow.step2_exchange(code)
        if callback:
            return callback(user, credentials)

    return google_api_callback