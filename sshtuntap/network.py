import pwd
from os import path
import ipaddress

import pymlconf


def getallhosts():
    # Look for all linux users using pwd module
    # filter users which has home dirs
    for i in pwd.getpwall():
        if i.pw_uid >= 1000 and not i.pw_shell.endswith('nologin'):
            configurationfile = path.join(i.pw_dir, '.ssh/tuntap')
            if not path.exists(configurationfile):
                continue

            yield i.pw_name, configurationfile



def assign():
    hosts = {}
    for u, c in getallhosts():
        hosts[u] = pymlconf.Root()
        hosts[u].loadfile(c)

    print(hosts)
    # hosts -> set(ip1, ip2, ..., ipn)

    # Find all hosts
    # create an ip network using ipaddress module
    net = ipaddress.IPv4Network('192.168.1.0/24')

    # find two free addresses
    for ip in net.hosts():
        if ip in addresses:
            continue

        if len(freeaddresses) >= 2:
            break

        freeaddresses.append(ip)

    return addresses


def addhost(username):
    ip1, ip2 = assign()


    # Fetch current network
    # Assign two new addresses
    # create or update the ~/.ssh/tuntap.yml
    # Network intnerfaces.d
    pass

