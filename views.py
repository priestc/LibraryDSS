from giotto.views import GiottoView, renders
from giotto.utils import jsonify

class ForceJSONView(GiottoView):
    @renders("*/*")
    def renderer(self, data, errors):
        return jsonify(data)

class ForceTextView(GiottoView):
    @renders("*/*")
    def renderer(self, data, errors):
        return self.text(data)