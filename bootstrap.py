#!/usr/bin/python

import os
import sys
import subprocess

if "VIRTUAL_ENV" not in os.environ:
    sys.stderr.write("$VIRTUAL_ENV not found.\n")
    sys.exit(-1)

virtualenv = os.environ["VIRTUAL_ENV"]
file_path = os.path.dirname(__file__)
subprocess.call(["pip", "install", "--upgrade", "-E", virtualenv, "--requirement",
    os.path.join(file_path, "requirements/apps.txt")])

