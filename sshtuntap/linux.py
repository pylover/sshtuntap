import pwd
import subprocess as sp


def userexists(name):
    try:
        return pwd.getpwnam(name)
    except KeyError:
        return False


def shell(cmd):
    print(f'Shell: {cmd}')
    return sp.run(cmd, shell=True, check=True, stdout=sp.PIPE, stderr=sp.PIPE)
