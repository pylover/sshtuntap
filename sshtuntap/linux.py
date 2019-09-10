import pwd


def userexists(name):
    try:
        return pwd.getpwnam(name)
    except KeyError:
        return False

