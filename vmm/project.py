#!/usr/bin/python

import os
import sys
import argparse
import copy
import yaml

from instance import Instance

class Project (dict):

    def __init__(self, *args, **kwargs):
        super(Project, self).__init__(*args, **kwargs)
        self.resolve_interfaces()

    @classmethod
    def load(cls, path):
        with open(path) as fd:
            return cls(yaml.load(fd)['project'])

    def resolve_interfaces(self):
        for instance in self.instances():
            for interface in instance.get('interfaces', []):
                interface.update(self['networks'][interface['network']])

    def instances(self):
        instances = self.get('instances', {})
        if 'default' in instances:
            default = instances['default']
        else:
            default = {}

        for name, data in instances.items():
            if name == 'default':
                continue

            data['name'] = name

            yield(Instance(copy.deepcopy(default).items() + data.items()))

if __name__ == '__main__':
    p = Project.load(sys.argv[1])

