#!/usr/bin/env python3
import re
from typing import Optional


class CompositeCommand:
    composite: str
    A: Optional[str]
    B: Optional[str]

    def __init__(self, composite: str, A: Optional[str], B: Optional[str]):
        self.composite = composite
        self.A = A
        self.B = B

    @staticmethod
    def from_str(command: str) -> 'CompositeCommand':
        A = None
        B = None
        # match case: c(A,B)
        r = re.match(
            r'^\s*([|+-]?[-_\w*]+)\s*\(\s*([-_\w*]+)\s*,\s*([-_\w*]+)\)\s*$', command)
        if r:
            A = r.group(2)
            B = r.group(3)
        else:
            # match case: c(A)
            r = re.match(r'^\s*([|+-]?[-_\w*]+)\s*\(\s*([-_\w*]+)\s*\)\s*$', command)
            if r:
                A = r.group(2)
            else:
                # match case: c
                r = re.match(r'^\s*([|+-]?[-_\w*]+)\s*$', command)
                assert r
        composite = r.group(1)
        if composite == '*':
            composite = None
        if A == '*':
            A = None
        if B == '*':
            B = None
        return CompositeCommand(composite,A,B)

    def modify(self, mod: str, reverse: bool=False) -> bool:
        # get command as string and process all replactions
        command = original = str(self)
        for r in mod.split(','):
            what, _with = r.split('->')
            if reverse:
                what, _with = _with, what
            command = command.replace(what.strip(), _with.strip())
        modified = original != command
        # re-convert string to command and take the elements
        command = CompositeCommand.from_str(command)
        self.composite = command.composite
        self.A = command.A
        self.B = command.B
        return modified

    def unmodify(self, mod: str) -> bool:
        return self.modify(mod, True)

    def __repr__(self) -> str:
        return "%s(%s,%s)" % (self.composite if self.composite else "*",
                               self.A if self.A else "*",
                               self.B if self.B else "*")

    def __eq__(self, other: object) -> bool:
        return ((self.composite == other.composite or not(self.composite and other.composite))
                and (self.A == other.A or not(self.A and other.A))
                and (self.B == other.B or not(self.B and other.B)))
