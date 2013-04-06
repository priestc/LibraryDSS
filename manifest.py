from giotto.programs import GiottoProgram, ProgramManifest
from giotto.programs.management import management_manifest
from giotto.views import GiottoView, BasicView, jinja_template

from models import Item, Library, configure
from views import ForceJSONView
from client import publish

manifest = ProgramManifest({
    'startPublish': GiottoProgram(
        controller=['http-post'],
        model=[Item.start_publish, {"name": "s3", 'access_key': 'AKIAJZFWR2UWSFJ6YXUQ', "secret_key": "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", "bucket_name": "library_chrispriest"}],
        view=ForceJSONView,
    ),
    'completePublish': GiottoProgram(
        controller=['http-post'],
        model=[Library.finish_publish, "OK"],
        view=BasicView,
    ),
    'query': GiottoProgram(
        model=[Library.query],
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
})