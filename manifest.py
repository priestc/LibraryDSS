from giotto.programs import GiottoProgram, ProgramManifest
from giotto.programs.management import management_manifest
from giotto.views import GiottoView, BasicView, jinja_template

from models import Item, Library, configure
from views import ForceJSONView
from client import publish
from server import finish_publish, start_publish, query

def test_wrapper():
    from test import functional_test
    functional_test()

manifest = ProgramManifest({
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
    'configure': GiottoProgram(
        model=[configure],
        view=BasicView(
            html=jinja_template("configure.html"),
        ),
    ),
    'publish': GiottoProgram(
        controller=['cmd'],
        model=[publish],
        view=BasicView,
    ),
    'mgt': management_manifest,
    'test': GiottoProgram(
        model=[test_wrapper],
        view=BasicView
    ),
})