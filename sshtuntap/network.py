import os
import pwd
from os import path, chown
from ipaddress import ip_address, IPv4Network

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:  # pragma: no cover
    from yaml import Loader

from .linux import shell
from .console import ok, warning, info


USER_CONFIGURATIONFILE = '.ssh/tuntap.yml'


def yamlload(s):
    return yaml.load(s, Loader)


def gethost(name):
    user = pwd.getpwnam(name)
    configurationfilename = path.join(user.pw_dir, USER_CONFIGURATIONFILE)
    if not path.exists(configurationfilename):
        raise KeyError(name)

    with open(configurationfilename) as f:
        return yamlload(f), configurationfilename


def getallhosts():
    # Look for all linux users using pwd module
    # filter users which has home dirs
    for i in pwd.getpwall():
        if i.pw_uid >= 1000 and not i.pw_shell.endswith('nologin'):
            configurationfile = path.join(i.pw_dir, USER_CONFIGURATIONFILE)
            if not path.exists(configurationfile):
                continue

            with open(configurationfile) as f:
                conf = yamlload(f)

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


def createinterface(host):
    index = str(host['index'])
    ifname = f'tun{index}'
    clientaddr = host['addresses']['client']
    serveraddr = host['addresses']['server']
    owner = host['remoteuser']
    lines = [f'{i}\n' for i in [
        f'allow-hotplug {ifname}',
        f'auto {ifname}',
        f'iface {ifname} inet static',
        f'  netmask 31',
        f'  pre-up ip tuntap add mode tun dev {ifname} user {owner} group {owner}',
        f'  pre-up ip address add dev {ifname} {serveraddr}/31 peer {clientaddr}/31',
    ]]

    ifacefilename = path.join('/etc/network/interfaces.d', ifname)
    with open(ifacefilename, 'w') as f:
        f.writelines(lines)

    ok(f'File {ifacefilename} has been created successfully.')

    shell(f'ip tuntap add mode tun dev {ifname} user {owner} group {owner}')
    shell(f'ip address add dev {ifname} {serveraddr}/31 peer {clientaddr}/31')
    shell(f'ip link set up dev {ifname}')


def addhost(network, user):
    configurationfile = path.join(user.pw_dir, USER_CONFIGURATIONFILE)
    if path.exists(configurationfile):
        warning(f'User is already exists: {user.pw_name}')
        warning(f'Overwriting the file: {configurationfile}')

    server, client, index = assign(network)
    info(f'Assigned addresses: {client} {server}')

    userconfiguration = dict(
        remoteuser=user.pw_name,
        uid=user.pw_uid,
        gid=user.pw_gid,
        shell=user.pw_shell,
        addresses=dict(client=str(client), server=str(server)),
        netmask=str(network.netmask),
        index=index
    )

    sshdirectory = path.dirname(configurationfile)
    if not path.exists(sshdirectory):
        os.mkdir(sshdirectory, mode=0o700)
        chown(sshdirectory, user.pw_uid, user.pw_gid)

    with open(configurationfile, 'w') as f:
        yaml.dump(userconfiguration, f, default_flow_style=False)

    chown(configurationfile, user.pw_uid, user.pw_gid)
    createinterface(userconfiguration)


def deletehost(username):
    host, configurationfilename = gethost(username)
    index = str(host['index'])
    ifname = f'tun{index}'
    shell(f'ifdown {ifname}')

    # remove the interfaces.d file
    ifacefilename = path.join('/etc/network/interfaces.d', ifname)
    if path.exists(ifacefilename):
        os.remove(ifacefilename)

    shell(f'ip tuntap delete {ifname} mode tun')

    # remove the .ssh/tuntap.yml file
    if path.exists(configurationfilename):
        os.remove(configurationfilename)

