import os
from os import path

import pymlconf
from easycli import SubCommand, Argument, Root


DEFAULT_CONFIGURATIONFILENAME = '/etc/sshtuntap.yml'
BUILTIN_CONFIGURATION = '''
cidr: 192.168.22.0/24
'''

settings = pymlconf.Root(BUILTIN_CONFIGURATION, context=os.environ)


class InfoCommand(SubCommand):
    __command__ = 'info'

    def __call__(self, args):
        print(f'CIDR: {settings.cidr}')


class SetupCommand(SubCommand):
    __command__ = 'setup'
    __arguments__ = [
        Argument('cidr', help='The network/mask (aka CIDR)')
    ]

    def __call__(self, args):

        settings.cidr = args.cidr
        with open(args.configurationfilename, 'w') as f:
            f.write(settings.dumps())

        ok(f'Settings are saved into {args.configurationfilename}')



class UserAddCommand(SubCommand):
    __command__ = 'add'
    __aliases__ = ['a']
    __arguments__ = [
        Argument('name'),
        Argument(
            '-m', '--mode',
            choices=['tun', 'tap'],
            default='tun',
            help='default: tun'
        )
    ]

    def __call__(self, args):
        username = args.name
        if linux.userexists(username):
            info(f'User {username} is already exists, ignoring.')

        linux.adduser(username)
        network.addhost(username)
        ok(f'User {username} was created successfully')


class UserCommand(SubCommand):
    __command__ = 'user'
    __aliases__ = ['u']
    __arguments__ = [
        UserAddCommand,
    ]


class ServerRoot(Root):
    __command__ = 'server'
    __aliases__ = ['s']
    __completion__ = True
    __arguments__ = [
        Argument(
            '-c', '--configurationfilename',
            metavar='FILENAME',
            default=DEFAULT_CONFIGURATIONFILENAME,
            help=f'default: {DEFAULT_CONFIGURATIONFILENAME}'
        ),
        Argument('-V', '--version', action='store_true'),
        InfoCommand,
        SetupCommand,
        UserCommand,
    ]

    def _execute_subcommand(self, args):
        filename = args.configurationfilename
        if path.exists(filename):
            settings.loadfile(filename)

        super()._execute_subcommand(args)

    def __call__(self, args):
        if args.version:
            print(__version__)


def main():
    ServerRoot().main()

