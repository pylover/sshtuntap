import os
from os import path

import pymlconf
from easycli import SubCommand, Argument, Root

from .console import info, ok, error, warning
from . import linux



HOME = os.environ['HOME']
USER = os.environ['USER']
DEFAULT_CONFIGURATIONFILENAME = f'{HOME}/.ssh/sshtuntap.yml'
BUILTIN_CONFIGURATION = f'''
hostname:
'''

settings = pymlconf.DeferredRoot()


def configure():
    settings.initialize(BUILTIN_CONFIGURATION, context=os.environ)


class InfoCommand(SubCommand):
    __command__ = 'info'

    def __call__(self, args):
        print(f'Configuration file: {args.configurationfilename}')
        print(f'CIDR: {settings.cidr}')


class SetupCommand(SubCommand):
    __command__ = 'setup'
    __arguments__ = [
        Argument('hostname', help=f'The server\'s hostname')
    ]

    def __call__(self, args):
        filename = args.configurationfilename
        hostname = args.hostname
        linux.shell(f'scp {USER}@{hostname}:.ssh/tuntap.yml {filename}')
        settings.loadfile(filename)
        settings.hostname = hostname

        with open(filename, 'w') as f:
            f.write(settings.dumps())

        ok(f'Settings are saved into {filename}')


class ClientRoot(Root):
    __aliases__ = ['c']
    __completion__ = True
    __arguments__ = [
        Argument(
            '-c', '--configurationfilename',
            metavar='FILENAME',
            default=DEFAULT_CONFIGURATIONFILENAME,
            help=f'default: {DEFAULT_CONFIGURATIONFILENAME}'
        ),
        Argument('-V', '--version', action='store_true'),
        SetupCommand,
    ]

    def _execute_subcommand(self, args):
        filename = args.configurationfilename
        configure()

        if path.exists(filename):
            settings.loadfile(filename)

        elif args.command not in ('setup', ):
            error(f'Configuration file does not exists: {filename}')
            return 1

        super()._execute_subcommand(args)

    def __call__(self, args):
        if args.version:
            from sshtuntap import __version__ as version
            print(version)
            return

        super().__call__(args)


def main():
    ClientRoot().main()

