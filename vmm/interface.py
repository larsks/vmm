#!/usr/bin/python

import os
import sys

import utils
from templates import env

defaults = {}

class Interface (dict):

    def __init__(self, *args, **kwargs):
        super(Interface, self).__init__(*args, **kwargs)

        for k,v in defaults.items():
            self.setdefault(k, v)

    def toxml(self):
        tmpl = env.get_template('interface.xml')
        return tmpl.render(interface=self)

