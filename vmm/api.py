#!/usr/bin/python

import os
import sys
import logging
import errno
import pprint

import libvirt
from lxml.builder import ElementMaker
from lxml import etree
from lxml import objectify

import utils

class API (object):
    def __init__(self, uri=None):
        if uri is None:
            uri = os.environ.get('LIBVIRT_DEFAULT_URI', 'qemu:///session')

        self.uri = uri
        self.setup_logging()
        self.setup_elementmaker()
        self.open_connection()

    def setup_elementmaker(self):
        self.elementmaker = ElementMaker()

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

    def attach_backing_store(self, disk, xml):
        E = self.elementmaker

        bs = disk['backing_store']

        if bs['type'] == 'volume':
            bvol = self.find_volume(bs['name'], bs['pool'])
            back = E.backingStore(
                    E.path(bvol.path()),
                    E.format(type=bs['format']),
                    )
        elif bs['type'] == 'file':
            back = E.backingStore(
                    E.path(bs['source']),
                    E.format(type=bs['format']),
                    )

        xml.append(back)

    def create_volume(self, disk):
        E = self.elementmaker

        size, unit = utils.parse_size(disk['size'])

        xml = E.volume(
                E.name(disk['name']),
                E.capacity(size, unit=unit),
                E.target(
                    E.format(type=disk.get('format', 'raw'))),
                )

        if 'backing_store' in disk:
            self.attach_backing_store(disk, xml)

        pool = self.find_pool(disk['pool'])
        self.log.debug('creating vol %s in pool %s',
                disk['name'], pool.name())
        vol = pool.createXML(etree.tostring(xml), 0)
        return vol

    def process_disks(self, instance):
        disks = []

        for disk in instance.disks:
            disk['name'] = disk['name'] % instance
            disk.setdefault('pool', 'default')

            self.log.info('processing volume %(name)s' % disk)

            if disk['type'] == 'file':
                continue

            if disk['type'] == 'volume':
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

                disk['type'] = 'file'
                disk['source'] = vol.path()
                disks.append(disk)

            instance['disks'] = disks

    def start(self, instance):
        self.process_disks(instance)

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

