#!/usr/bin/python
"""
Script to anonymize QIF data by randomizing it's input.

For development and demonstration purposes only.
"""

import sys
from os import urandom
from random import random, choice
from binascii import hexlify


UNIQUES = set()
FAKE_ACCOUNTS = [
    ('Counterparty 1', 'LU11 1111 1234 0001 0000'),
    ('Counterparty 2', 'LU11 1111 1234 0002 0000'),
    ('Counterparty 3', 'LU11 1111 1234 0003 0000'),
    ('Counterparty 4', 'LU11 1111 1234 0004 0000'),
    ('Counterparty 5', 'LU11 1111 1234 0005 0000'),
    ('Counterparty 6', 'LU11 1111 1234 0006 0000'),
    ('Counterparty 7', 'LU11 1111 1234 0007 0000'),
    ('Counterparty 8', 'LU11 1111 1234 0008 0000'),
]


def rchar():
    rdata = urandom(10)
    while rdata in UNIQUES:
        rdata = urandom(10)
    UNIQUES.add(rdata)
    return hexlify(rdata)


def process_file(fp):
    for line in fp:
        line = line.strip()
        if line.startswith('M'):
            print('MMessage %s' % rchar())
        elif line.startswith('N'):
            print('NMC%s' % rchar())
        elif line[0] in ('D', '^'):
            print(line)
        elif line[0] == 'T':
            print('T%.3f' % (random() * 1000 - 500))
        elif line[0] == 'P':
            print('P%s (%s)' % choice(FAKE_ACCOUNTS))

with open(sys.argv[1]) as fp:
    process_file(fp)

# P Payee (IBAN)

# T Amount
# D Date
# ^
# M Memo
# N Check Number
