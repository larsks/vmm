#!/usr/bin/python

import os
import sys
import jinja2
import jinja2.loaders

env = jinja2.Environment(
        loader=jinja2.loaders.PackageLoader('vmm'))

