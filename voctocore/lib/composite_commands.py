#!/usr/bin/env python3
import re


class CompositeCommand:

    def __init__(self, composite, A, B):
        self.composite = composite
        self.A = A
        self.B = B

    def from_str(command):
        A = None
        B = None
        # match case: c(A,B)
        r = re.match(
            r'^\s*([-_\w*]+)\s*\(\s*([-_\w*]+)\s*,\s*([-_\w*]+)\)\s*$', command)
        if r:
            A = r.group(2)
            B = r.group(3)
        else:
            # match case: c(A)
            r = re.match(r'^\s*([-_\w*]+)\s*\(\s*([-_\w*]+)\s*\)\s*$', command)
            if r:
                A = r.group(2)
            else:
                # match case: c
                r = re.match(r'^\s*([-_\w*]+)\s*$', command)
                assert r
        composite = r.group(1)
        if composite == '*':
            composite = None
        if A == '*':
            A = None
        if B == '*':
            B = None
        return CompositeCommand(composite,A,B)

    def __str__(self):
        return "%s(%s,%s)'" % (self.composite if self.composite else "*",
                               self.A if self.A else "*",
                               self.B if self.B else "*")

    def __eq__(self, other):
        return ((self.composite == other.composite or not(self.composite and other.composite))
                and (self.A == other.A or not(self.A and other.A))
                and (self.B == other.B or not(self.B and other.B)))
