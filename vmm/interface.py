#!/usr/bin/python

import os
import sys
from lxml import etree
import jinja2
import jinja2.loaders

import utils

defaults = {}

class Interface (dict):

    def __init__(self, *args, **kwargs):
        super(Interface, self).__init__(*args, **kwargs)

        for k,v in defaults.items():
            self.setdefault(k, v)

        self.env = jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('vmm'))

    def toxml(self):
        tmpl = self.env.get_template('interface.xml')
        return tmpl.render(interface=self)

