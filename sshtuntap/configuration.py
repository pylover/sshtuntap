import os
from os import path

import pymlconf
from easycli import SubCommand, Argument, Root


settings = pymlconf.DeferredRoot()

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


def configure():
    settings.initialize(BUILTIN_CONFIGURATION, context=os.environ)

