from giotto.programs import Program, Manifest
from giotto.programs.management import management_manifest
from giotto.control import Redirection
from giotto.views import GiottoView, BasicView, jinja_template, URLFollower, ForceJSONView
from giotto.contrib.auth.middleware import AuthenticationMiddleware, AuthenticatedOrDie, NotAuthenticatedOrRedirect
from giotto.contrib.auth.manifest import create_auth_manifest
from giotto.contrib.static.programs import StaticServe
from giotto.primitives import LOGGED_IN_USER
from giotto import get_config

from models import Item, Library, configure
import client
import server

from giotto_dropbox.manifest import make_dropbox_manifest
from giotto_google.manifest import make_google_manifest

from third_party_callbacks import dropbox_api_callback, google_api_callback

def test_wrapper():
    from test import functional_test
    # not committed because it contains secret API keys
    functional_test()

class AuthenticationRequiredProgram(Program):
    pre_input_middleware = [AuthenticationMiddleware, AuthenticatedOrDie]

class AuthenticationProgram(Program):
    pre_input_middleware = [AuthenticationMiddleware]

def post_register_callback(user):
    """
    After a new user signs up, create a Library for them.
    """
    session = get_config('db_session')
    l = Library(identity="%s@%s" % (user.username, get_config('domain')))
    session.add(l)
    session.commit()

manifest = Manifest({
    '': '/landing',
    'landing': AuthenticationProgram(
        input_middleware=[NotAuthenticatedOrRedirect('/ui/dashboard')],
        model=[server.home],
        view=BasicView(
            html=jinja_template('landing.html'),
        ),
    ),
    'apps': Manifest({
        'camera': Program(
            view=BasicView(
                html=jinja_template("camera.html"),
            ),
        ),
        'blog': Program(
            view=BasicView(
                html=jinja_template("blog.html"),
            ),
        ),
        'music': Program(
            view=BasicView(
                html=jinja_template("music.html")
            ),
        )
    }),
    'auth': create_auth_manifest(
        post_register_callback=post_register_callback,
    ),
    'backup': Program(
        model=[server.backup],
        view=ForceJSONView
    ),
    'acceptConnectionRequest': AuthenticationRequiredProgram(
        model=[server.accept_connection_request],
        view=BasicView(
            html=lambda m: Redirection('/ui/connections')
        )
    ),
    'ui': Manifest({
        'autocomplete': Program(
            model=[server.autocomplete],
            view=BasicView,
        ),
        'items': AuthenticationProgram(
            description="HTML page for looking at items and querying them",
            model=[server.items],
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
                model=[server.edit_item],
                view=BasicView(),
            ),
        ],
        'dashboard': AuthenticationRequiredProgram(
            model=[server.dashboard],
            view=BasicView(
                html=jinja_template('dashboard.html')
            )
        ),
        'connections': [
            AuthenticationRequiredProgram(
                controllers=['http-get'],
                model=[server.show_connections],
                view=BasicView(
                    html=jinja_template("connections.html")
                )
            ),
            AuthenticationRequiredProgram(
                controllers=['http-post'],
                model=[server.connection_submit],
                view=BasicView(
                    html=Redirection('/ui/connections')
                )
            )
        ],
        'addS3': AuthenticationRequiredProgram(
            model=[server.addS3],
            view=BasicView(
                html=Redirection('/engines'),
            ),
        ),
    }),
    'api': Manifest({
        'startPublish': AuthenticationProgram(
            controllers=['http-post'],
            model=[server.start_publish],
            view=ForceJSONView,
        ),
        'completePublish': AuthenticationProgram(
            controllers=['http-post'],
            model=[server.finish_publish, "OK"],
            view=BasicView,
        ),
        'requestAuthorization': Program(
            description="API Endpoint for incoming authorization requests",
            controllers=['http-post'],
            model=[server.request_authorization],
            view=BasicView,
        ),
        'query': Program(
            model=[server.execute_query],
        )

    }),
    'engines': Manifest({
        '': AuthenticationRequiredProgram(
            model=[server.engine_dashboard],
            view=BasicView(
                html=jinja_template('engines.html'),
            ),
        ),
        'update_engine': AuthenticationRequiredProgram(
            controllers=['http-post'],
            model=[server.update_engine],
            view=BasicView,
        ),
        'migrate_off_engine': AuthenticationRequiredProgram(
            model=[server.migrate_off_engine],
            view=BasicView,
        ),
        'migrate_onto_engine': AuthenticationRequiredProgram(
            model=[server.migrate_onto_engine],
            view=BasicView,
        ),
    }),
    'google': make_google_manifest(
        scheme='https',
        auth_program_class=AuthenticationRequiredProgram,
        post_auth_callback=google_api_callback
    ),
    'dropbox': make_dropbox_manifest(
        auth_program_class=AuthenticationRequiredProgram,
        post_auth_callback=dropbox_api_callback,
    ),
    'publish': Program(
        controllers=['cmd'],
        model=[client.publish],
        view=BasicView,
    ),
    'query': Program(
        controllers=['cmd'],
        model=[client.query],
        view=BasicView,
    ),
    'mgt': management_manifest,
    'test': Manifest({
        'integration': Program(
            # run a quick and dirty test to see if everything is working.
            model=[test_wrapper],
            view=BasicView
        ),
        'lql_parse': Program(

        ),
    }),
    'static': StaticServe(),
})