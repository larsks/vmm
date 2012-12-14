#!/usr/bin/python

import os
import sys
from lxml import etree
import jinja2
import jinja2.loaders

import utils

bus2dev = {
        'virtio': 'vda',
        'ide': 'hda',
        'scsi': 'sda',
        'sata': 'sda',
        'usb': 'sda',
        }

defaults = {
        'bus': 'virtio',
        }

class Disk (dict):

    def __init__(self, *args, **kwargs):
        super(Disk, self).__init__(*args, **kwargs)

        for k,v in defaults.items():
            self.setdefault(k, v)

        self.env = jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('vmm'))

    @property
    def size(self):
        disk_size, disk_unit = utils.parse_size(self['size'])
        return utils.adjust_size(int(disk_size), disk_unit)

    @property
    def device(self):
        return bus2dev[self['bus']]

    def toxml(self):
        tmpl = self.env.get_template('disk.xml')
        return tmpl.render(disk=self)

