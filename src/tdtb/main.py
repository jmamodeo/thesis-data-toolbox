import argparse

from tdtb.commands.addtasks import addtasks
from tdtb.commands.procrec import procrec
from tdtb.commands.searchms import searchms
from tdtb.commands.searchks import searchks
from tdtb.commands.unittables import unittables

COMMANDS = {
    'addtasks': addtasks,
    'procrec': procrec,
    'searchms': searchms,
    'searchks': searchks,
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
