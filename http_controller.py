#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
from giotto import initialize

import config
initialize(config)

from manifest import manifest

mock = '--model-mock' in sys.argv
from giotto.controllers.http import make_app, error_handler, serve

application = make_app(manifest, model_mock=mock)

if not config.debug:
    application = error_handler(application)

if '--run' in sys.argv:
    serve('127.0.0.1', 5000, application, use_debugger=True, use_reloader=True)