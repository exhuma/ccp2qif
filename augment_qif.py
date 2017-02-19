"""
Some QIF files do not contain any account information. This little script is
used to inject account information into such files.

It uses a "hints" file to determine the account number from file name. It's a
JSON file with the following structure:

    {
        "acct_number": ["hint1", "hint2", ...],
        ...
    }

If the filename contains any one of the hints, the matching account number is
used.

If the file does not exist, it's automatically created.

The QIF files and hints file must be in the same folder. All QIF files in that
folder will be processed. The original file will be written as a '.bak' file.
"""

from glob import glob
from json import load, dump
from os.path import exists, basename, join
from shutil import move
import sys




def process(filename, hints):

    print('Processing %s' % filename)
    with open(filename) as fp:
        data = fp.read()

    for line in data.splitlines():
        line = line.strip()
        if line.startswith('!Account'):
            has_account_identifier = True
            break
    else:
        has_account_identifier = False

    if not has_account_identifier:
        for account_number, guesses in hints.items():
            if any([guess.lower() in filename.lower() for guess in guesses]):
                guessed_account = account_number
                break
        else:
            guessed_account = ''

        account_number = input(
            'Account Number [%s]: ' % guessed_account).strip()

        if not account_number and not guessed_account:
            raise ValueError('Must have an account number!')
        elif not account_number and guessed_account:
            account_number = guessed_account

        account_hints = set(hints.setdefault(account_number, []))
        account_hints.add(basename(filename))
        hints[account_number] = list(account_hints)
        move(filename, filename + '.bak')
        with open(filename, 'w') as outfile:
            outfile.write(u'!Account\n')
            outfile.write(u'N{}\n'.format(account_number))
            outfile.write(u'TBank\n')
            outfile.write(u'^\n')

            # Copy the remaining data
            outfile.write(data)


def main(folder):
    hints_file = join(folder, 'hints.json')
    if exists(hints_file):
        hints = load(open(hints_file))
    else:
        hints = {}
    for filename in glob(join(folder, '*.qif')):
        process(filename, hints)
        dump(hints, open(hints_file, 'w'), indent=4)


if __name__ == '__main__':
    if sys.version_info < (3, 0):
        print("Python 3 required!", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(main(sys.argv[1]))
