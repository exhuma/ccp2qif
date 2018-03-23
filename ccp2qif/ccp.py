from collections import namedtuple
from datetime import datetime
from decimal import Decimal
import codecs
import csv

from schwifty import IBAN

from ccp2qif.model import QIFTransaction, AccountInfo, TransactionList
from ccp2qif.util import UnicodeReader, account_name_from_filename


DataRow = namedtuple(
    'DataRow',
    'accounting_date, '
    'description, '
    'amount, '
    'currency, '
    'value_date, '
    'counterparty_account, '
    'counterparty_name, '
    'communication_1, '
    'communication_2, '
    'operation_reference')


def try_getting_account_number(line: str) -> str:
    if line.lower().startswith('account number'):
        account_info = line.split(';')
        raw_account_number = account_info[1]
        try:
            account_number = IBAN(raw_account_number)
        except ValueError:
            return None
        else:
            return account_number.formatted
    else:
        return None


def clean_join(record, fields):
    """
    Join only fields which have a value
    """
    return '; '.join([record[_] for _ in fields if record[_].strip()])


def to_qif(record: DataRow) -> QIFTransaction:
    message = clean_join(record._asdict(),
                         ('communication_1', 'communication_2', 'description'))
    counterparty = clean_join(record,
                              ('counterparty_name', 'counterparty_account'))
    output = QIFTransaction(
        record.value_date,
        record.amount,
        message,
        counterparty
    )
    # TODO if record['operation_reference']:
    # TODO     lines.append(u'N{operation_reference}')
    return output


def parse(infile):
    raw_account_info = next(infile)
    _, account_number, _ = raw_account_info.split(';')
    next(infile)  # column names
    reader = csv.reader(infile, delimiter=';', quotechar='"')
    account_info = AccountInfo(account_number, '')
    transactions = []
    for row in reader:
        transactions.append(QIFTransaction(
            datetime.strptime(row[4], '%d-%m-%Y').date(),
            Decimal(row[2].replace(',', '.')),
            '%s | %s | %s' % (row[1], row[7], row[8]),
            row[5],
        ))
        # TODO row[9]  # reference
    return TransactionList(account_info, transactions)


def convert_csv(source_filename, target_filename, account_name=None):
    with open(source_filename, 'r') as csvfile:
        with codecs.open(target_filename, 'w', encoding='utf8') as outfile:

            # If the file contains a line with account info, this overrides the
            # rest.
            account_line = csvfile.readline()
            account_number = try_getting_account_number(account_line)
            if account_number:
                print('Account number %r found in file. Overriding manual '
                      'value' % account_number)
                account_name = account_number

            if account_name:
                outfile.write('!Account\n')
                outfile.write('N{0}\n'.format(account_name))
                outfile.write('TBank\n')
                outfile.write('^\n')
            outfile.write(u'!Type:Bank\n')

            csvfile.readline()  # skip header
            csvreader = UnicodeReader(csvfile, delimiter=';', quotechar='"',
                                      encoding='latin1')
            for row in csvreader:
                record = DataRow(*row)
                outfile.write(to_qif(record._asdict()))
                print(u'Wrote {0.accounting_date} - {0.communication_1}'.format(
                    record).encode('utf8'))


def convert_excel(source_filename, target_filename, account_name):
    from xlrd import open_workbook, xldate_as_tuple
    from datetime import date
    if not account_name:
        raise ValueError('Account name is required for Excel exports!')
    book = open_workbook(source_filename)
    sheet = book.sheet_by_index(0)
    with codecs.open(target_filename, 'w', encoding='utf8') as outfile:
        outfile.write('!Account\n')
        outfile.write('N{0}\n'.format(account_name))
        outfile.write('TBank\n')
        outfile.write('^\n')
        outfile.write(u'!Type:Bank\n')
        for row_index in range(1, sheet.nrows):
            line = [sheet.cell(row_index, col_index).value
                    for col_index in range(sheet.ncols)]
            acdate_value, opdate_value, card_number, description, _, amount = line
            opdate_value = date(*xldate_as_tuple(opdate_value, book.datemode)[:3])
            acdate_value = date(*xldate_as_tuple(acdate_value, book.datemode)[:3])
            record = DataRow(
                acdate_value,
                description,
                amount,
                'EUR',
                opdate_value,
                'unspecified',
                '',
                '',
                '',
                '',
            )
            outfile.write(to_qif(record._asdict()))
            print(u'Wrote {0.value_date} - {0.description}'.format(
                record).encode('utf8'))
