#!/usr/bin/python

import os
import sys
import re

multiplier = {
    'B':    1,
    'K':    2**10,
    'KiB':  2**10,
    'KB':   10**3,
    'M':    2**20,
    'MB':   2**20,
    'MiB':  10**6,
    'G':    2**30,
    'GiB':  2**30,
    'GB':   10**9,
    'T':    2**40,
    'TiB':  2**40,
    'TB':   10**12,
    'PB':   2**50,
    'PiB':  2**50,
    'P':    10**15,
    'EB':   2**60,
    'EiB':  2**60,
    'E':    10**18,
    }

def parse_size(size):
    mo = re.match('(\d+)\s*(bytes|B|K|KiB|KB|M|MB|MiB|G|GiB|GB|T|TB|TiB|PB|P|PiB|EB|E|EiB|)$', size)
    if not mo:
        raise ValueError(size)
    return mo.group(1), mo.group(2)

def adjust_size(size, unit):
    return size * multiplier[unit]

