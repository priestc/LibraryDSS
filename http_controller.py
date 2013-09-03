#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
from giotto import initialize

import config
import secrets
import machine
initialize(config, secrets, machine)
from giotto import get_config

import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config"

from manifest import manifest

mock = '--model-mock' in sys.argv
from giotto.controllers.http import make_app, fancy_error_template_middleware, serve

application = make_app(manifest, model_mock=mock)

if not get_config('debug'):
    application = fancy_error_template_middleware(application)

if '--run' in sys.argv:
    serve('127.0.0.1', 80, application, ssl=None, use_debugger=True, use_reloader=True)

if '--run-ssl' in sys.argv:
    ctx = ('/Users/chris/Documents/key.crt', '/Users/chris/Documents/key.key')
    serve('127.0.0.1', 443, application, ssl=ctx, use_debugger=True, use_reloader=True)