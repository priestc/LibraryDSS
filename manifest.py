from giotto.programs import GiottoProgram, ProgramManifest
from giotto.programs.management import management_manifest
from giotto.views import GiottoView, BasicView, jinja_template, URLFollower
from giotto.contrib.auth.middleware import AuthenticationMiddleware, AuthenticatedOrDie
from giotto.contrib.auth.manifest import create_auth_manifest
from giotto.contrib.static.programs import StaticServe
from giotto.primitives import LOGGED_IN_USER
from giotto import get_config

from models import Item, Library, configure
from views import ForceJSONView
from client import publish
from server import (finish_publish, start_publish, query, manage,
    google_api_callback, backup,
    settings, migrate_off_engine, update_engine, migrate_onto_engine, home)

from config import project_path

from giotto_dropbox.manifest import make_dropbox_manifest
from giotto_google.manifest import make_google_manifest

from third_party import dropbox_api_callback, google_api_callback

def test_wrapper():
    from test import functional_test
    # not committed because it contains secret API keys
    functional_test()

class AuthenticationRequiredProgram(GiottoProgram):
    pre_input_middleware = [AuthenticationMiddleware, AuthenticatedOrDie]

def post_register_callback(user):
    """
    After a new user signs up, create a Library for them.
    """
    session = get_config('session')
    l = Library(identity=user.username)
    session.add(l)
    session.commit()

manifest = ProgramManifest({
    '': 'home',
    'home': GiottoProgram(
        input_middleware=[AuthenticationMiddleware],
        model=[home],
        view=BasicView(
            html=jinja_template('home.html')
        ),
    ),
    'auth': create_auth_manifest(
        post_register_callback=post_register_callback,
    ),
    'startPublish': GiottoProgram(
        controller=['http-post'],
        model=[start_publish],
        view=ForceJSONView,
    ),
    'completePublish': GiottoProgram(
        controller=['http-post'],
        model=[finish_publish, "OK"],
        view=BasicView,
    ),
    'query': GiottoProgram(
        model=[query],
        view=BasicView,
    ),
    'backup': GiottoProgram(
        model=[backup],
        view=ForceJSONView
    ),
    'configure': GiottoProgram(
        # API endpoint for changing library settings.
        model=[configure],
        view=BasicView(
            html=jinja_template("configure.html"),
        ),
    ),
    'manage': AuthenticationRequiredProgram(
        # HTML page for looking at contents and adding storag engines
        model=[manage],
        view=BasicView(
            html=jinja_template("manage.html"),
        )
    ),
    'settings': ProgramManifest({
        '': AuthenticationRequiredProgram(
            model=[settings],
            view=BasicView(
                html=jinja_template('settings.html'),
            ),
        ),
        'update_engine': AuthenticationRequiredProgram(
            controllers=['http-post'],
            model=[update_engine],
            view=BasicView,
        ),
        'migrate_off_engine': AuthenticationRequiredProgram(
            model=[migrate_off_engine],
            view=BasicView,
        ),
        'migrate_onto_engine': AuthenticationRequiredProgram(
            model=[migrate_onto_engine],
            view=BasicView,
        ),
    }),
    'google': make_google_manifest(
        auth_program_class=AuthenticationRequiredProgram,
        post_auth_callback=google_api_callback
    ),
    'dropbox': make_dropbox_manifest(
        auth_program_class=AuthenticationRequiredProgram,
        post_auth_callback=dropbox_api_callback,
    ),
    'publish': GiottoProgram(
        controller=['cmd'],
        model=[publish],
        view=BasicView,
    ),
    'mgt': management_manifest,
    'test': GiottoProgram(
        # run a quick and dirty test to see if everything is working.
        model=[test_wrapper],
        view=BasicView
    ),
    'urltest': GiottoProgram(
        model=[lambda: "http://google.com"],
        view=URLFollower(),
    ),
    'static': StaticServe(project_path + '/static/'),
})