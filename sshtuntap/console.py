import sys

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'



def ok(msg):
    print(f'{colors.OKGREEN}{msg}{colors.RESET}')


def info(*args):
    print(*args)


def error(msg):
    print(f'{colors.FAIL}{msg}{colors.RESET}', file=sys.stderr)


