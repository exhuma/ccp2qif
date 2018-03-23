from __future__ import print_function
from collections import namedtuple
from functools import partial
from os.path import splitext
from typing import TextIO
import codecs
import sys

from schwifty import IBAN

from ccp2qif.util import UnicodeReader
from ccp2qif.model import QIFTransaction, TransactionList, AccountInfo
import ccp2qif.bil
import ccp2qif.ccp


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
        with open(source_filename) as infile:
            parser = mod.sniff(infile)
        if parser:
            break

    if not parser:
        raise ValueError('No valid parser found')

    with open(source_filename) as infile:
        data = parser(infile, account_name)

    with open(target_filename, 'w') as out:
        write_qif(data, out)
        print('Written to %r' % target_filename)


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
