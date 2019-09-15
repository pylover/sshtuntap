import pwd
from os import path
from ipaddress import ip_address, IPv4Network

import yaml

from .configuration import settings
from .exceptions import UserExistsError


USER_CONFIGURATIONFILE = '.ssh/tuntap.yml'


def getallhosts():
    # Look for all linux users using pwd module
    # filter users which has home dirs
    for i in pwd.getpwall():
        if i.pw_uid >= 1000 and not i.pw_shell.endswith('nologin'):
            configurationfile = path.join(i.pw_dir, USER_CONFIGURATIONFILE)
            if not path.exists(configurationfile):
                continue

            with open(configurationfile) as f:
                conf = yaml.load(f)

            yield i.pw_name, conf


def getallassignedaddresses():
    for u, c in getallhosts():
        yield ip_address(c['addresses']['client'])
        yield ip_address(c['addresses']['server'])


def assign(network):
    addresses = set(getallassignedaddresses())
    result = []

    # find two free addresses
    for ip in network.hosts():
        if ip in addresses:
            continue

        if len(result) >= 2:
            break

        result.append(ip)

    client, server = result
    return client, server, int(client) - int(network.network_address)


def getnetwork():
    return IPv4Network(settings.cidr)


def addhost(user):
    configurationfile = path.join(user.pw_dir, USER_CONFIGURATIONFILE)
    if path.exists(configurationfile):
        raise UserExistsError()

    network = getnetwork()
    client, server, index = assign(network)
    print(client, server)

    userconfiguration = dict(
        name=user.pw_name,
        shell=user.pw_shell,
        addresses=dict(client=str(client), server=str(server)),
        index=index
    )

    with open(configurationfile, 'w') as f:
        yaml.dump(userconfiguration, f, default_flow_style=False)

    # Network intnerfaces.d

