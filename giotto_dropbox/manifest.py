from giotto.programs import GiottoProgram, ProgramManifest
from giotto.views import URLFollower
from models import make_callback_model

def make_dropbox_manifest(auth_program_class=None, post_auth_callback=None):
    """
    Use this function to create a manifest object. Pass in a function
    GiottoProgram subclass that imlplements auth. Also pass in a callback
    function for execution after authentication successful.
    """
    if not auth_program_class:
        auth_program_class = GiottoProgram

    callback_model = make_callback_model(post_auth_callback)

    return ProgramManifest({
        'oauth1callback': auth_program_class(
            model=[callback_model],
            view=URLFollower(),
        )
    })