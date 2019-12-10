import pwd
import subprocess as sp


def userexists(name):
    try:
        return pwd.getpwnam(name)
    except KeyError:
        return False


def shell(cmd, check=True):
    print(f'Shell: {cmd}')
    return sp.run(cmd, shell=True, check=check)  #, stdout=sp.PIPE, stderr=sp.PIPE)

def deletesystemdservice(instance):
    shell(f'systemctl stop {instance}.service')
    shell(f'systemctl disable {instance}.service')
    shell(f'rm /etc/systemd/system/{instance}.service')
    shell('systemctl daemon-reload')

def createsystemdservice(instance, content):
    with open(f'/etc/systemd/system/{instance}.service', 'w') as f:
        f.write(content)

    shell('systemctl daemon-reload')
    shell(f'systemctl enable {instance}.service')
    shell(f'systemctl start {instance}.service')



