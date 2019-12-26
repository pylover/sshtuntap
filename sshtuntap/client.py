import os
import time
import socket
import struct
import argparse
import traceback
import signal
from os import path
from subprocess import CalledProcessError, Popen

import pymlconf
from easycli import SubCommand, Argument, Root

from .console import info, ok, error, warning
from .linux import shell



HOME = os.environ['HOME']
USER = os.environ['USER']
DEFAULT_CONFIGURATIONFILENAME = f'{HOME}/.ssh/tuntap.yml'
BUILTIN_CONFIGURATION = f'''
hostname:
localuser:
'''

settings = pymlconf.DeferredRoot()


class SSHRetryError(Exception):
    pass

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
        if USER == 'root':
            error('Do not run this command by the root user')
            return 1

        filename = args.configurationfilename
        hostname = args.hostname
        shell(f'scp {hostname}:.ssh/tuntap.yml {filename}')
        settings.loadfile(filename)
        settings.hostname = \
            hostname.split('@')[1] if '@' in hostname else hostname
        settings.localuser = USER

        with open(filename, 'w') as f:
            f.write(settings.dumps())

        ok(f'Settings are saved into {filename}')


class ConnectCommand(SubCommand):
    __command__ = 'connect'
    __aliases__ = ['c']
    __arguments__ = [
        Argument('-v', '--verbose', action='store_true', help='Verbose'),
        Argument(
            '-r', '--retrymax',
            type=int,
            default=0,
            help='Maximum retry, default is: 0, infinite!'
        ),
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

    def connect(self, gateway, hostaddr, hostname, args):
        index = settings.index
        hostname = settings.hostname
        remoteuser = settings.remoteuser
        localuser = settings.localuser
        serveraddr = settings.addresses.server
        terminating = False
        c = args.retrymax
        infinite = c == 0
        sshargs = []

        if args.verbose:
            sshargs.append('-v')

        sshargs.append(f'-o"ServerAliveInterval 10"')
        sshargs.append(f'-o"ServerAliveCountMax 1"')
        sshargs.append(f'-o"ConnectTimeout 10"')
        sshargs.append(f'-o"ConnectionAttempts 20"')

        def term(sig, frame):
            nonlocal terminating
            terminating = True
            os.killpg(os.getpgid(sshprocess.pid), signal.SIGTERM)

        signal.signal(signal.SIGTERM, term)
        signal.signal(signal.SIGINT, term)

        while infinite or (c > 0):
            try:
                shell(f'ip route replace {hostaddr} via {gateway}')
                shell(f'ip route replace default via {serveraddr}')
                sshprocess = Popen(
                    f'sudo -u {localuser} ssh {remoteuser}@{hostname} ' \
                    f'-Nw {index}:{index} {" ".join(sshargs)}',
                    shell=True,
                    preexec_fn=os.setsid,
                )
                sshprocess.wait()

                if terminating or sshprocess.returncode <= 0:
                    break

            finally:
                shell(f'ip route del {hostaddr} via {gateway}', check=False)
                shell(f'ip route replace default via {gateway}', check=False)

            time.sleep(1)
            c -= 1

    def __call__(self, args):
        if USER != 'root':
            error('Please run this command as root.')
            return 1

        hostname = settings.hostname
        remoteuser = settings.remoteuser
        localuser = settings.localuser
        index = settings.index
        ifname = f'tun{index}'
        clientaddr = settings.addresses.client
        serveraddr = settings.addresses.server
        netmask = settings.netmask
        hostaddr = socket.gethostbyname(hostname)

        gateway = self.getdefaultgateway()
        if gateway is None:
            error(f'Invalid default gateway: {gateway}')

        try:
            shell(f'ip tuntap add mode tun dev {ifname} user {localuser} group {localuser}')
            shell(
                f'ip address add dev {ifname} {clientaddr}/{netmask} ' \
                f'peer {serveraddr}/{netmask}'
            )
            shell(f'ip link set up dev {ifname}')
            self.connect(gateway, hostaddr, hostname, args)
        finally:
            info('Terminating...')
            shell(f'ip tuntap delete mode tun dev {ifname}', check=False)


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

        elif args.command not in ('setup', 'completion'):
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

