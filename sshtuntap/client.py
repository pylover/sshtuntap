import os
import socket
import struct
from os import path
import argparse

import pymlconf
from easycli import SubCommand, Argument, Root

from .console import info, ok, error, warning
from .linux import shell



HOME = os.environ['HOME']
USER = os.environ['USER']
DEFAULT_CONFIGURATIONFILENAME = f'{HOME}/.ssh/tuntap.yml'
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
        shell(f'scp {USER}@{hostname}:.ssh/tuntap.yml {filename}')
        settings.loadfile(filename)
        settings.hostname = hostname

        with open(filename, 'w') as f:
            f.write(settings.dumps())

        ok(f'Settings are saved into {filename}')


class ConnectCommand(SubCommand):
    __command__ = 'connect'
    __aliases__ = ['c']
    __arguments__ = [
        Argument('-v', '--verbose', action='store_true', help='Verbose')
    ]

    def getdefaultgateway(self):
        """Returns the current default gateway from `/proc`
        """
        with open('/proc/net/route') as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

    def __call__(self, args):
        hostname = settings.hostname
        user = settings.name
        index = settings.index
        ifname = f'tun{index}'
        clientaddr = settings.addresses.client
        serveraddr = settings.addresses.server
        netmask = settings.netmask
        gateway = self.getdefaultgateway()
        hostaddr = socket.gethostbyname(hostname)
        sshargs = []

        if args.verbose:
            sshargs.append('-v')

        try:
            shell(f'ip tuntap add mode tun dev {ifname}')
            shell(
                f'ip address add dev {ifname} {clientaddr}/{netmask} ' \
                f'peer {serveraddr}'
            )
            shell(f'ip link set up dev {ifname}')
            shell(f'ip route add {hostaddr} via {gateway}')
            shell(f'ip route replace default via {serveraddr}')
            shell(
                f'sudo -u {user} ssh {user}@{hostname} -Nw {index}:{index} ' \
                f'{" ".join(sshargs)}'
            )
        finally:
            shell(f'ip tuntap delete mode tun dev {ifname}')
            shell(f'ip route del {hostaddr} via {gateway}')
            shell(f'ip route replace default via {gateway}')


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
        ConnectCommand,
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

