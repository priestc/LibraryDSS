from models import get_flow
from giotto.primitives import ALL_DATA, LOGGED_IN_USER

def make_google_manifest(post_auth_callback=None):
    def google_api_callback(code, all=ALL_DATA, user=LOGGED_IN_USER):
        """
        After authenticating with the Google API Auth server, it redirects the user
        back to this program, where `code` is exchanged for an auth token, and
        then stored.
        """
        flow = get_flow()
        credentials = flow.step2_exchange(code)
        if post_auth_callback:
            return post_auth_callback(user, credentials)

    return google_api_callback