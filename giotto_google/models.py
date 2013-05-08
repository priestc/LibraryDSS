from oauth2client.client import flow_from_clientsecrets
from giotto import get_config

def get_google_flow():
    return flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/drive',
        redirect_uri='%s/google/oauth2callback' % get_config("server_url"),
    )