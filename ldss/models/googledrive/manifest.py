from giotto.primitives import ALL_DATA, LOGGED_IN_USER
from giotto.programs import Program, Manifest
from giotto.views import URLFollower

from models import make_callback_model

def make_google_manifest(scheme='http', auth_program_class=None, post_auth_callback=None):
    """
    Use this function to create a manifest object. Pass in a function
    Program subclass that imlplements auth. Also pass in a callback
    function for execution after authentication successful.
    """
    if not auth_program_class:
        auth_program_class = Program

    callback_model = make_callback_model(scheme=scheme, callback=post_auth_callback)

    return Manifest({
        'oauth2callback': auth_program_class(
            model=[callback_model],
            view=URLFollower(),
        )
    })