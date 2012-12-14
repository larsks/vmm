#!/usr/bin/python

import os
import sys
import logging
import argparse

from project import Project
from api import API

log = None

def cmd_down(opts, project, api):
    for i in project.instances():
        if opts.names and not i['name'] in opts.names:
            continue

        log.warn('stopping %s', i['name'])
        try:
            api.stop(i, keep=opts.keep)
        except KeyError:
            continue

def cmd_up(opts, project, api):
    for i in project.instances():
        if opts.names and not i['name'] in opts.names:
            continue

        log.warn('starting %s', i['name'])
        api.start(i)

def cmd_dumpxml(opts, project, api):
    for i in project.instances():
        if opts.names and not i['name'] in opts.names:
            continue

        log.warn('starting %s', i['name'])
        print i.toxml()

def cmd_status(opts, project, api):
    for i in project.instances():
        if opts.names and not i['name'] in opts.names:
            continue

        print i['name'], api.status(i)

def cmd_suspend(opts, project, api):
    pass

def cmd_resume(opts, project, api):
    pass

def cmd_migrate(opts, project, api):
    pass

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v', action='store_true')
    p.add_argument('--debug', action='store_true')
    p.add_argument('--connect', '-c',
            help='libvirt connect uri, defaults to LIBVIRT_DEFAULT_URI if set, otherwise qemu:///session')
    p.add_argument('--config', '-f', default='instances.yml')

    s = p.add_subparsers()

    p_up = s.add_parser('up')
    p_up.add_argument('names', nargs='*')
    p_up.set_defaults(handler=cmd_up)

    p_down = s.add_parser('down')
    p_down.add_argument('--keep', '-k',
            action='store_true',
            help='Do not delete storage volumes')
    p_down.add_argument('names', nargs='*')
    p_down.set_defaults(handler=cmd_down)

    p_dumpxml = s.add_parser('dumpxml')
    p_dumpxml.add_argument('names', nargs='*')
    p_dumpxml.set_defaults(handler=cmd_dumpxml)

    p_status = s.add_parser('status')
    p_status.add_argument('names', nargs='*')
    p_status.set_defaults(handler=cmd_status)

    p_suspend = s.add_parser('suspend')
    p_suspend.add_argument('names', nargs='*')
    p_suspend.set_defaults(handler=cmd_suspend)

    p_resume = s.add_parser('resume')
    p_resume.add_argument('names', nargs='*')
    p_resume.set_defaults(handler=cmd_resume)

    p_migrate = s.add_parser('migrate')
    p_migrate.add_argument('--live', action='store_true')
    p_migrate.add_argument('--p2p', action='store_true')
    p_migrate.add_argument('--tunneled', action='store_true')
    p_migrate.add_argument('--shared', action='store_true')
    p_migrate.add_argument('--desturi', '-d')
    p_migrate.add_argument('names', nargs='*')
    p_migrate.set_defaults(handler=cmd_migrate)

    return p.parse_args()

def main():
    global project
    global log

    opts = parse_args()

    if opts.debug:
        level = logging.DEBUG
    elif opts.verbose:
        level=logging.INFO
    else:
        level=logging.WARN

    project = Project.load(opts.config)
    api = API(opts.connect)

    logging.basicConfig(
            level=level,
            format='%(asctime)s %(name)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            )

    log = logging.getLogger('vmm')

    opts.handler(opts, project, api)

if __name__ == '__main__':
    main()


