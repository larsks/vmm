#!/usr/bin/python

import os
import sys

import utils
from templates import env

defaults = {
        'bus': 'virtio',
        }

class Disk (dict):

    def __init__(self, *args, **kwargs):
        super(Disk, self).__init__(*args, **kwargs)

        for k,v in defaults.items():
            self.setdefault(k, v)

    @property
    def size(self):
        disk_size, disk_unit = utils.parse_size(self['size'])
        return utils.adjust_size(int(disk_size), disk_unit)

    def toxml(self):
        tmpl = env.get_template('disk.xml')
        return tmpl.render(disk=self)

