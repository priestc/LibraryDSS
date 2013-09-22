from giotto.programs import Program, Manifest
from giotto.programs.management import management_manifest
from giotto.views import BasicView

manifest = Manifest({
    '': Program(
        model=[lambda: "Welcome to Giotto!"],
        view=BasicView
    ),
    'mgt': management_manifest,
})