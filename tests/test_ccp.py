from datetime import date
from decimal import Decimal
from io import StringIO

from ccp2qif.ccp import parse
from ccp2qif.core import (
    AccountInfo,
    QIFTransaction as QT,
    TransactionList,
    write_qif,
)


def test_parsing():
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
        result = parse(infile)
    assert result.account == expected.account
    assert result.transactions == expected.transactions
    assert result == expected


def test_to_qif():
    with open('testdata/ccp/ccp_in.csv') as infile:
        input_data = parse(infile)
    with open('testdata/ccp/ccp_out.qif') as infile:
        expected = infile.read()
    output = StringIO()
    write_qif(input_data, output)
    result = output.getvalue()
    print(result)
    assert result == expected
