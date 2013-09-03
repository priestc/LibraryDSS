#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
from giotto import initialize

import config
import secrets
import machine
initialize(config, secrets, machine)

import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config"

from manifest import manifest

args = sys.argv
mock = '--model-mock' in args
if mock:
    # remove the mock argument so the controller doesn't get confused
    args.pop(args.index('--model-mock'))
from giotto.controllers.cmd import CMDController, CMDRequest
request = CMDRequest(sys.argv)
controller = CMDController(request=request, manifest=manifest, model_mock=mock)
controller.get_response()