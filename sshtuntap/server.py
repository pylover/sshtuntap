import os
import pwd
from os import path

import pymlconf
from easycli import SubCommand, Argument, Root

from .console import info, ok, error, warning
from .texteditor import TextFile
from .configuration import configure, settings
from . import network
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
            warning('please restart the openssh-server.')

        else:
            ok(f'PermitTunnel is already enabled in {sshdfile.filename}.')

        sshdfile.saveifneeded()


class HostAddCommand(SubCommand):
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
        hostname = args.name
        try:
            host = pwd.getpwnam(hostname)
        except KeyError:
            error(f'Host {hostname} is not exists, please create it first.')
            return 1

        network.addhost(host)
        ok(f'Host {hostname} was created successfully')


class HostListCommand(SubCommand):
    __command__ = 'list'
    __aliases__ = ['l']

    def __call__(self, args):
        for u, c in network.getallhosts():
            addrs = c['addresses']
            info(addrs['client'], addrs['server'], u)


class HostDeleteCommand(SubCommand):
    __command__ = 'delete'
    __aliases__ = ['d', 'del']
    __arguments__ = [
        Argument('name'),
    ]

    def __call__(self, args):
        hostname = args.name
        try:
            network.deletehost(hostname)
        except KeyError:
            error(f'Host: {hostname} is not exists.')
        else:
            ok(f'Host {hostname} has been deleted successfully')


class HostCommand(SubCommand):
    __command__ = 'hosts'
    __aliases__ = ['h', 'host']
    __arguments__ = [
        HostAddCommand,
        HostListCommand,
        HostDeleteCommand,
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
        HostCommand,
    ]

    def _execute_subcommand(self, args):
        filename = args.configurationfilename
        configure()

        if path.exists(filename):
            settings.loadfile(filename)

        elif args.command not in ('setup', 'install'):
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

