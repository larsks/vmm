#!/usr/bin/python

import os
import sys
from lxml.builder import ElementMaker
from lxml import etree
import jinja2
import jinja2.loaders

import utils
from disk import Disk
from interface import Interface

defaults = {
        'machine': 'pc-0.15',
        'arch': 'x86_64',
        'vcpu': '1',
        'features': [
            'acpi',
            'apic',
            'pae',
            ],
        'emulator': '/usr/bin/qemu-kvm',
        'graphics': {
            'type': 'vnc',
            'port': '-1',
            'autoport': 'yes',
            },
        'video': {
            'type': 'cirrus',
            'vram': '9216',
            'heads': '1',
            },
        'disk': {
            'bus': 'virtio',
            }
        }

bus2dev = {
        'virtio': 'vda',
        'ide': 'hda',
        'scsi': 'sda',
        }

class Instance (dict):

    def __init__(self, *args, **kwargs):
        super(Instance, self).__init__(*args, **kwargs)

        for k,v in defaults.items():
            self.setdefault(k, v)

        self.elementmaker = ElementMaker()
        self.env = jinja2.Environment(
                loader=jinja2.loaders.PackageLoader('vmm'))

    @property
    def memory(self):
        mem_size, mem_unit = utils.parse_size(self['memory'])
        return utils.adjust_size(int(mem_size), mem_unit)

    @property
    def sysarch(self):
        return os.uname()[4]

    @property
    def disks(self):
        for disk in self.get('disks', []):
            yield Disk(disk)

    @property
    def interfaces(self):
        for interface in self.get('interfaces', []):
            yield Interface(interface)

    def device(self, bus):
        return bus2dev[bus]

    def toxml(self):
        tmpl = self.env.get_template('domain.xml')
        return tmpl.render(dom=self)

if __name__ == '__main__':
    i = Instance(
            name='test',
            memory='1G',
            disks=[
                {'source': '/tmp/disk.img', 'format': 'qcow2'},
                ],
            graphics = {
                'type': 'spice',
                }
            )

    print i.toxml()

