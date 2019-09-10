import re

from .console import info

CR = '\n'

class TextFile:
    def __init__(self, filename):
        self.filename = filename
        self.isdirty = False
        with open(filename) as f:
            self.lines = [l.rstrip('\r\n') for l in f.readlines()]

    def save(self):
        with open(self.filename, 'w') as f:
            f.write(CR.join(self.lines))

        self.isdirty = False

    def saveifneeded(self):
        if self.isdirty:
            self.save()

    def __iter__(self):
        yield from enumerate(self.lines)

    def matchinglines(self, pattern):
        p = re.compile(pattern)
        for i, line in self:
            if p.match(line):
                yield i, line

    def commentout(self, pattern, commentchar='#'):
        out = []
        for i, line in self.matchinglines(pattern):
            self.lines[i] = f'{commentchar}{line}'
            self.isdirty = True
            warning(f'Line {i} was commented in file: {self.filename}')
            info(line)

    def hasline(self, pattern):
        return any(self.matchinglines(pattern))

    def append(self, s):
        self.lines += s.splitlines()
        self.isdirty = True

