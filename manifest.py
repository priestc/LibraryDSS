from giotto.programs import GiottoProgram, ProgramManifest
from giotto.programs.management import management_manifest
from giotto.views import GiottoView, BasicView, jinja_template, URLFollower, ForceJSONView
from giotto.contrib.auth.middleware import AuthenticationMiddleware, AuthenticatedOrDie
from giotto.contrib.auth.manifest import create_auth_manifest
from giotto.contrib.static.programs import StaticServe
from giotto.primitives import LOGGED_IN_USER
from giotto import get_config

from models import Item, Library, configure
from client import publish, query
from server import (finish_publish, start_publish, items, backup,
    settings, migrate_off_engine, update_engine, migrate_onto_engine, home,
    edit_item)

from config import project_path

from giotto_dropbox.manifest import make_dropbox_manifest
from giotto_google.manifest import make_google_manifest

from third_party_callbacks import dropbox_api_callback, google_api_callback

def test_wrapper():
    from test import functional_test
    # not committed because it contains secret API keys
    functional_test()

class AuthenticationRequiredProgram(GiottoProgram):
    pre_input_middleware = [AuthenticationMiddleware, AuthenticatedOrDie]

class AuthenticationProgram(GiottoProgram):
    pre_input_middleware = [AuthenticationMiddleware]

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
            html=jinja_template('home.html'),
        ),
    ),
    'apps': ProgramManifest({
        'camera': GiottoProgram(
            view=BasicView(
                html=jinja_template("camera.html"),
            ),
        ),
        'blog': GiottoProgram(
            view=BasicView(
                html=jinja_template("blog.html"),
            ),
        ),
    }),
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
    'items': AuthenticationProgram(
        # HTML page for looking at items and querying them
        model=[items],
        view=BasicView(
            html=jinja_template("items.html"),
        ),
    ),
    'item': [
        AuthenticationRequiredProgram(
            controllers=['http-get'],
            model=[Item.get],
            view=BasicView(
                html=jinja_template('single_item.html'),
            ),
        ),
        AuthenticationRequiredProgram(
            controllers=['http-post'],
            model=[edit_item],
            view=BasicView(),
        ),
    ],
    'engines': ProgramManifest({
        '': AuthenticationRequiredProgram(
            model=[settings],
            view=BasicView(
                html=jinja_template('engines.html'),
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
        controllers=['cmd'],
        model=[publish],
        view=BasicView,
    ),
    'query': GiottoProgram(
        controllers=['cmd'],
        model=[query],
        view=BasicView,
    ),
    'mgt': management_manifest,
    'test': ProgramManifest({
        'integration': GiottoProgram(
            # run a quick and dirty test to see if everything is working.
            model=[test_wrapper],
            view=BasicView
        ),
        'lql_parse': GiottoProgram(

        ),
    }),
    'static': StaticServe('/static/'),
})