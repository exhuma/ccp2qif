import logging
from collections import namedtuple
from datetime import datetime, date
from decimal import Decimal
from xlrd import open_workbook, xldate_as_tuple
import csv

from schwifty import IBAN

from ccp2qif.model import QIFTransaction, AccountInfo, TransactionList


LOG = logging.getLogger(__name__)


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


def sniff(file_pointer):
    LOG.debug('Trying to detect file-type using %s', __name__)
    file_pointer.seek(0)
    try:
        magic = file_pointer.read(17)
    except Exception as exc:
        LOG.debug('Unable to read from file (%s)!', exc)
        magic = None
    file_pointer.seek(0)
    if magic == 'Account number :;':
        return parse_csv

    # Assuming excel file
    book = open_workbook(file_pointer.name)
    sheet = book.sheet_by_index(0)
    row = sheet.row(0)
    book.release_resources()
    del book
    if len(row) == 6 and row[-2].value == 'Original amount':
        return parse_xls_2
    return None


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
        counterparty,
        record.operation_reference
    )
    return output


def parse_xls(infile, account_number='unknown'):
    account_info = AccountInfo(account_number, '')
    book = open_workbook(infile)
    sheet = book.sheet_by_index(0)
    transactions = []
    for row_index in range(1, sheet.nrows):
        line = [sheet.cell(row_index, col_index).value
                for col_index in range(sheet.ncols)]
        acdate_value, description, cp_acct, cp_name, amount = line
        acdate_value = date(*xldate_as_tuple(acdate_value, book.datemode)[:3])
        transactions.append(QIFTransaction(
            acdate_value,
            Decimal('%.2f' % amount),
            description,
            cp_acct,
            ''
        ))
    return TransactionList(account_info, transactions)


def parse_xls_2(infile, account_number='unknown'):
    '''
    Parses another XLS format detected on the exports. This format is used for
    prepaid VISA cards.

    Columns:

        * Accounting date
        * Operation date
        * Card number
        * Description
        * Original amount
        * Amount EUR
    '''

    account_info = AccountInfo(account_number, '')
    book = open_workbook(infile.name)
    sheet = book.sheet_by_index(0)
    transactions = []
    for row_index in range(1, sheet.nrows):
        line = [sheet.cell(row_index, col_index).value
                for col_index in range(sheet.ncols)]
        acdate, op_date, card_no, description, orig_amount, real_amount = line
        acdate = date(*xldate_as_tuple(acdate, book.datemode)[:3])
        op_date = date(*xldate_as_tuple(op_date, book.datemode)[:3])
        transactions.append(QIFTransaction(
            acdate,
            Decimal('%.2f' % real_amount),
            description,
            '',
            ''
        ))
    return TransactionList(account_info, transactions)


def parse_csv(infile, account_number=''):
    raw_account_info = next(infile)
    _, account_number, _ = raw_account_info.split(';')
    next(infile)  # column names
    reader = csv.reader(infile, delimiter=';', quotechar='"')
    account_info = AccountInfo(account_number, '')
    transactions = []
    for row in reader:
        desc = row[1].strip()
        comm1 = row[7].strip()
        comm2 = row[8].strip()
        cp_acct = row[5].strip()
        cp_name = row[6].strip()
        reference = row[9]

        message_fields = [desc, comm1, comm2]
        cp_fields = [cp_acct, cp_name]
        message = ' | '.join([fld for fld in message_fields if fld])
        counterparty = ' | '.join([fld for fld in cp_fields if fld])
        transactions.append(QIFTransaction(
            datetime.strptime(row[4], '%d-%m-%Y').date(),
            Decimal(row[2].replace('.', '').replace(',', '.')),
            message,
            counterparty,
            reference
        ))
    return TransactionList(account_info, transactions)
