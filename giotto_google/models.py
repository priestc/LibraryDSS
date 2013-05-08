from oauth2client.client import flow_from_clientsecrets
from giotto import get_config
from giotto.primitives import ALL_DATA, LOGGED_IN_USER

def get_google_flow():
    return flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/drive',
        redirect_uri='%s/google/oauth2callback' % get_config("server_url"),
    )

def make_callback_model(callback):
    def google_api_callback(code, all=ALL_DATA, user=LOGGED_IN_USER):
        """
        After authenticating with the Google API Auth server, it redirects the user
        back to this program, where `code` is exchanged for an auth token, and
        then stored.
        """
        flow = get_google_flow()
        credentials = flow.step2_exchange(code)
        if callback:
            return callback(user, credentials)

    return google_api_callback