from __future__ import print_function
from collections import namedtuple
from functools import partial
from os.path import splitext
from typing import TextIO
import codecs
import logging
import sys

from gouge.colourcli import Simple
from schwifty import IBAN

from ccp2qif.util import UnicodeReader
from ccp2qif.model import QIFTransaction, TransactionList, AccountInfo
import ccp2qif.bil
import ccp2qif.ccp


LOG = logging.getLogger(__name__)


def write_qif(transaction_list: TransactionList, outfile: TextIO,
              datefmt: str = '%d/%m/%Y'):
    '''
    Converts a transaction list to a QIF file
    '''
    write = partial(print, file=outfile)
    write('!Account')
    write('N%s' % transaction_list.account.account_number)
    write('D"%s"' % transaction_list.account.description)
    write('TBank')
    write('^')
    write('!Type:Bank')
    for transaction in transaction_list.transactions:
        LOG.debug('Writing transaction at %s to %r',
                  transaction.date, outfile.name)
        write('D%s' % transaction.date.strftime(datefmt))
        write('T%s' % transaction.value)
        write('M%s' % transaction.message)
        if transaction.counterparty:
            write('P%s' % transaction.counterparty)
        if transaction.reference:
            write('N%s' % transaction.reference)
        write('^')


def convert(source_filename, target_filename, account_name=None):
    _, _, extension = source_filename.lower().rpartition('.')

    parser = None
    for mod in (ccp2qif.bil, ccp2qif.ccp):
        LOG.debug('Probing %r with %r', source_filename, mod)
        with open(source_filename) as infile:
            try:
                parser = mod.sniff(infile)
            except Exception:
                LOG.debug('Module %r was unable to process %r',
                          mod, source_filename, exc_info=True)
                continue
        if parser:
            break

    if not parser:
        raise ValueError('No parser found for %r' % source_filename)

    LOG.debug('Selected parser: %s:%s', parser.__module__, parser.__name__)
    if not parser:
        raise ValueError('No valid parser found')

    with open(source_filename) as infile:
        data = parser(infile, account_name)

    with open(target_filename, 'w') as out:
        write_qif(data, out)
        LOG.info('Written to %r' % target_filename)


def setup_logging(args):
    Simple.basicConfig(level=logging.DEBUG)


def climain():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-n', '--account-name', dest='account_name',
                        help='The name of the account for this import',
                        default=None)
    parser.add_argument('-o', '--outfile', dest='outfile',
                        help='The output file.', default=None)
    parser.add_argument('infile', nargs=1)
    args = parser.parse_args()
    setup_logging(args)

    if args.outfile:
        outfile = args.outfile
    else:
        base, ext = splitext(args.infile[0])
        if ext.lower() == 'qif':
            print('Error: The input file seems to be a qif file already!',
                  file=sys.stderr)
            return 9
        outfile = '{0}.qif'.format(base)

    convert(args.infile[0],
            outfile,
            account_name=args.account_name)
