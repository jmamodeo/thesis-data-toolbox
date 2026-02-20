import argparse

from tdtb.commands.alltasks import alltasks
from tdtb.commands.procrec import procrec
from tdtb.commands.searchms import searchms
from tdtb.commands.unittables import unittables


COMMANDS = {
    'alltasks': alltasks,
    'procrec': procrec,
    'searchms': searchms,
    'unittables': unittables,
}

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'command', 
        choices=COMMANDS.keys(), 
        help='Command to run',
    )

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    COMMANDS[args.command]()


if __name__ == '__main__':
    main()
