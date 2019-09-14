import os
from os import path

import pymlconf
from easycli import SubCommand, Argument, Root

from .console import info, ok, error, warning
from .texteditor import TextFile
from .configuration import configure, settings
from . import linux


DEFAULT_CIDR = '192.168.22.0/24'
ROOT = os.environ.setdefault('SSHTUNTAPSERVER_ROOT', '/').rstrip('/')
DEFAULT_CONFIGURATIONFILENAME = os.environ.setdefault(
    'SSHTUNTAPSERVER_CONFIGURATIONFILE',
    f'{ROOT}/etc/sshtuntap.yml'
)
SSHSERVER_CONFIGURATIONFILENAME = os.environ.setdefault(
    'SSHTUNTAPSERVER_SSHSERVERlCONFIGURATIONFILE',
    f'{ROOT}/etc/ssh/sshd_config'
)
SSHDSETTINGS = '''
# Added by sshtuntap-server
PermitTunnel yes
'''


BUILTIN_CONFIGURATION = f'''
cidr: {DEFAULT_CIDR}
'''


class InfoCommand(SubCommand):
    __command__ = 'info'

    def __call__(self, args):
        print(f'Configuration file: {args.configurationfilename}')
        print(f'CIDR: {settings.cidr}')


class SetupCommand(SubCommand):
    __command__ = 'setup'
    __arguments__ = [
        Argument(
            'cidr',
            nargs='?',
            default=DEFAULT_CIDR,
            help=f'The network/mask (aka CIDR), default: {DEFAULT_CIDR}'
        )
    ]

    def __call__(self, args):

        settings.cidr = args.cidr
        with open(args.configurationfilename, 'w') as f:
            f.write(settings.dumps())

        ok(f'Settings are saved into {args.configurationfilename}')

        sshdfile = TextFile(SSHSERVER_CONFIGURATIONFILENAME)
        sshdfile.commentout('PermitTunnel (?!yes)')

        if not sshdfile.hasline('PermitTunnel yes'):
            sshdfile.append(SSHDSETTINGS)

            ok(
                f'The following lines are added into the ' \
                f'{SSHSERVER_CONFIGURATIONFILENAME}'
            )
            info(SSHDSETTINGS)
            warning('Do you want to restart the openssh-server?')
            if input('You may restart the SSH server manualy ' \
                'if you choose no[Y/n]:') in ('y', 'Y'):

                print('Restarting ssh server...')
        else:
            ok(f'PermitTunnel is already enabled in {sshdfile.filename}.')

        sshdfile.saveifneeded()


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
        if not linux.userexists(username):
            info(f'User {username} is exists, ignoring.')

        network.addhost(username)
        ok(f'User {username} was created successfully')


class UserCommand(SubCommand):
    __command__ = 'user'
    __aliases__ = ['u']
    __arguments__ = [
        UserAddCommand,
    ]


class ServerRoot(Root):
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
        configure()

        if path.exists(filename):
            settings.loadfile(filename)

        elif args.command != 'setup':
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
    ServerRoot().main()

