#!/usr/bin/env python
# coding: utf-8
from giotto import initialize, get_config
initialize("ldss")

from ldss.manifest import manifest

import sys
mock = '--model-mock' in sys.argv
from giotto.controllers.http import make_app, fancy_error_template_middleware, serve

application = make_app(manifest, model_mock=mock)

if not get_config('debug'):
    application = fancy_error_template_middleware(application)

if '--run' in sys.argv:
    serve('127.0.0.1', 5000, application, ssl=None, use_debugger=True, use_reloader=True)

if '--run-ssl' in sys.argv:
    serve('127.0.0.1', 443, application, ssl='adhoc', use_debugger=True, use_reloader=True)
