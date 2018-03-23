from datetime import date
from decimal import Decimal
from io import StringIO

from ccp2qif.ccp import parse_csv, parse_xls
from ccp2qif.core import (
    AccountInfo,
    QIFTransaction as QT,
    TransactionList,
    write_qif,
)


def test_parsing_csv():
    cp_account = 'LU23 4567 8901 2345 1234'
    expected = TransactionList(
        account=AccountInfo('LU12 3456 7890 1234 5678', ''),
        transactions=[
            QT(date(2017, 1, 2), Decimal('-16.70'),
               'description 1 | comm 1-1 | comm 1-2', cp_account, 'ref 1'),
            QT(date(2017, 1, 2), Decimal('20.10'),
               'description 2 | comm 2-1 | comm 2-2', cp_account, 'ref 2'),
            QT(date(2017, 1, 3), Decimal('-20.00'),
               'description 3 | comm 3-1 | comm 3-2', cp_account, 'ref 3'),
            QT(date(2017, 1, 4), Decimal('-20.00'),
               'description 4 | comm 4-1 | comm 4-2', cp_account, 'ref 4'),
            QT(date(2017, 1, 5), Decimal('500'),
               'description 5 | comm 5-1 | comm 5-2', cp_account, 'ref 5'),
        ]
    )

    with open('testdata/ccp/ccp_in.csv') as infile:
        result = parse_csv(infile)
    assert result.account == expected.account
    assert result.transactions == expected.transactions
    assert result == expected


def test_parsing_xls():
    expected = TransactionList(
        account=AccountInfo('foo', ''),
        transactions=[
            QT(date(2018, 3, 23), Decimal('-18.90'), 'Desc 1', 'LU12 2345 1111 2222 0001', ''),
            QT(date(2018, 3, 23), Decimal('-2.90'), 'Desc 2', 'LU12 2345 1111 2222 0002', ''),
            QT(date(2018, 3, 21), Decimal('200.00'), 'Desc 3', 'LU12 2345 1111 2222 0003', ''),
            QT(date(2018, 3, 21), Decimal('-11.40'), 'Desc 4', 'LU12 2345 1111 2222 0004', ''),
            QT(date(2018, 3, 21), Decimal('-19.20'), 'Desc 5', 'LU12 2345 1111 2222 0005', ''),
            QT(date(2018, 3, 20), Decimal('-2.90'), 'Desc 6', 'LU12 2345 1111 2222 0006', ''),
        ]
    )


    result = parse_xls('testdata/ccp/ccp_in.xlsx', 'foo')
    assert result.account == expected.account
    assert result.transactions == expected.transactions
    assert result == expected


def test_to_qif():
    with open('testdata/ccp/ccp_in.csv') as infile:
        input_data = parse_csv(infile)
    with open('testdata/ccp/ccp_out.qif') as infile:
        expected = infile.read()
    output = StringIO()
    write_qif(input_data, output)
    result = output.getvalue()
    print(result)
    assert result == expected
