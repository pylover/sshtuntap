import pwd
from os import path

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
    hosts = pymlconf.Root()
    for u, c in getallhosts():
        hosts[u] = pymlconf.Root()
        hosts[u].loadfile(c)

    print(hosts)

    # Find all hosts
    # create a ip network using ipaddress module
    # find two free addresses
    # return them
    pass


def addhost(username):

    # Fetch current network
    # Assign two new addresses
    # create or update the ~/.ssh/tuntap.yml
    # Network intnerfaces.d
    pass
