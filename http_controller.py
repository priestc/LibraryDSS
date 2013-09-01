#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
from giotto import initialize

import config
import secrets
import machine
initialize(config, secrets, machine)

from manifest import manifest

mock = '--model-mock' in sys.argv
from giotto.controllers.http import make_app, error_handler, serve

application = make_app(manifest, model_mock=mock)

if not config.debug:
    application = error_handler(application)

if '--run' in sys.argv:
    serve('127.0.0.1', 80, application, ssl=None, use_debugger=True, use_reloader=True)

if '--run-ssl' in sys.argv:
    serve('127.0.0.1', 443, application, ssl='adhoc', use_debugger=True, use_reloader=True)