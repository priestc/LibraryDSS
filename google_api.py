from oauth2client.client import flow_from_clientsecrets

def get_flow():
    from giotto import get_config
    return flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/drive',
        redirect_uri='%s/google/oauth2callback' % get_config("server_url"),
    )