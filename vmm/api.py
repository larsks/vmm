#!/usr/bin/python

import os
import sys
import logging
import errno
import libvirt
from lxml import etree
from lxml import objectify

import utils
from templates import env

domain_states = {
        libvirt.VIR_DOMAIN_NOSTATE: 'none',
        libvirt.VIR_DOMAIN_RUNNING: 'running',
        libvirt.VIR_DOMAIN_BLOCKED: 'blocked',
        libvirt.VIR_DOMAIN_PAUSED: 'paused',
        libvirt.VIR_DOMAIN_SHUTDOWN: 'shutdown',
        libvirt.VIR_DOMAIN_SHUTOFF: 'shutoff',
        libvirt.VIR_DOMAIN_CRASHED: 'crashed',
        libvirt.VIR_DOMAIN_PMSUSPENDED: 'pmsuspend',
        }

device_prefix = {
        'virtio': 'vd',
        'scsi': 'sd',
        'sata': 'sd',
        'usb': 'sd',
        'ide': 'hd',
        }


class API (object):
    def __init__(self, uri=None):
        if uri is None:
            uri = os.environ.get('LIBVIRT_DEFAULT_URI', 'qemu:///session')

        self.uri = uri

        self.setup_logging()
        self.open_connection()

    def setup_logging(self):
        self.log = logging.getLogger('vmm.api')

    def open_connection(self):
        self.conn = libvirt.open(self.uri)

    def find_domain(self, name):
        try:
            dom = self.conn.lookupByName(name)
        except libvirt.libvirtError, detail:
            if detail.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                raise KeyError(name)
            else:
                raise

        return dom

    def suspend_domain(self, name):
        try:
            dom = self.find_domain(name)
            self.log.warn('suspending domain %s', name)
            dom.suspend()
        except KeyError:
            self.log.debug('attempt to suspend undefined domain %s', name)
            pass

    def resume_domain(self, name):
        try:
            dom = self.find_domain(name)
            self.log.warn('resuming domain %s', name)
            dom.resume()
        except KeyError:
            self.log.debug('attempt to resume undefined domain %s', name)
            pass

    def status(self, name):
        try:
            dom = self.find_domain(name)
            state, reason = dom.state(0)
            return ('active' if dom.isActive()  else 'inactive',
                    domain_states.get(state, state), state)
        except KeyError:
            return ('undefined', None, None)

    def find_pool(self, name):
        pool = self.conn.storagePoolLookupByName(name)
        return pool

    def find_volume(self, name, pool=None):
        if pool is None:
            pool = 'default'

        pool = self.find_pool(pool)
        try:
            vol = pool.storageVolLookupByName(name)
        except libvirt.libvirtError, detail:
            if detail.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                raise KeyError(name)
            else:
                raise

        return vol

    def resolve_volume(self, disk):
        if disk['type'] == 'volume':
            vol = self.find_volume(disk['name'], disk['pool'])
            disk['path'] = vol.path()
            disk['type'] = 'file'

    def create_volume(self, disk):
        size, unit = utils.parse_size(disk['size'])
        if 'backing_store' in disk:
            self.resolve_volume(disk['backing_store'])

        xml = env.get_template('volume.xml').render(
                vol=disk)
        pool = self.find_pool(disk['pool'])
        self.log.debug('creating vol %s in pool %s',
                disk['name'], pool.name())
        vol = pool.createXML(xml, 0)
        return vol

    def process_disks(self, instance):
        disks = []
        devices = {}

        for disk in instance.disks:
            devnum = devices.setdefault(disk['bus'], 0)
            devices[disk['bus']] = devnum + 1
            disk['device'] = device_prefix[disk['bus']] + chr(ord('a') + devnum)

            if disk['type'] == 'file':
                pass
            elif disk['type'] == 'block':
                disk.setdefault('format', 'raw')
            elif disk['type'] == 'volume':
                disk['name'] = disk['name'] % instance
                disk.setdefault('pool', 'default')

                self.log.debug('looking for vol %s in pool %s',
                        disk['name'], disk['pool'])
                try:
                    vol = self.find_volume(disk['name'], disk['pool'])
                    self.log.debug('found vol %s in pool %s',
                        disk['name'], disk['pool'])
                except KeyError:
                    self.log.debug('vol %s in pool %s not found',
                        disk['name'], disk['pool'])
                    vol = self.create_volume(disk)
                    disk['created'] = 1

                disk['type'] = 'file'
                disk['source'] = vol.path()

            self.log.info('added disk %(source)s' % disk)
            disks.append(disk)

            instance['disks'] = disks

    def start(self, instance):
        self.process_disks(instance)
        print instance.toxml()

        try:
            dom = self.find_domain(instance['name'])
        except KeyError:
            self.log.debug('defining domain %(name)s' % instance)
            dom = self.conn.defineXML(instance.toxml())

        self.log.warn('starting domain %(name)s' % instance)
        dom.create()

    def stop(self, instance, keep=False):
        domain = self.find_domain(instance['name'])
        if domain.isActive():
            domain.destroy()
        if not keep:
            self.purge_storage(domain)
        self.log.info('undefine %(name)s' % instance)
        domain.undefine()

    def purge_storage(self, domain):
        domxml = objectify.fromstring(domain.XMLDesc(0))
        for disk in domxml.devices.disk:
            path = disk.source.get('file')
            try:
                vol = self.conn.storageVolLookupByPath(path)
                self.log.warn('deleting volume %s', path)
                vol.delete(0)
            except libvirt.libvirtError, detail:
                if not detail.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                    raise()

                try:
                    os.unlink(path)
                except OSError, detail:
                    if not detail.errno == errno.ENOENT:
                        raise

