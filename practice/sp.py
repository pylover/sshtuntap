import os
import sys
import time
from subprocess import *
from signal import *


def term(sig, frame):
    global p
    print(f'sending signal: {sig}')
    os.killpg(os.getpgid(p.pid), SIGTERM)


def main():
    global p

    signal(SIGTERM, term)
    signal(SIGINT, term)
    p = Popen(
        'ssh banana -vN',
        shell=True,
        stdout=PIPE,
        preexec_fn=os.setsid,
    )
    print(os.getpid(), p.pid)
    p.wait()
#    while True:
#        r = popen.poll()
#        if r is None:
#            time.sleep(.4)
#            continue
#
#        return r

    print(p.returncode)


if __name__ == '__main__':
    sys.exit(main())

