# for debug logging
import logging
# use Frame
from lib.frame import Frame, X, Y, L, T, R, B
# for cloning objects
import copy
# for parsing configuration items
import re

log = logging.getLogger('Composites')


class Composites:
    """ a namespace for composite related methods
    """

    def configure(cfg, size, add_swap=True):
        """ read INI like configuration from <cfg> and return all the defined
            composites. <size> is the overall frame size which all proportional
            (floating point) coordinates are related to.
        """
        # prepare resulting composites dictonary
        composites = dict()
        # walk through composites configuration
        for c_name, c_val in cfg:
            if '.' not in c_name:
                raise RuntimeError("syntax error in composite config '{}' "
                                   "(must be: 'name.attribute')"
                                   .format(c_name))
            # split name into name and attribute
            name, attr = c_name.lower().rsplit('.', 1)
            if name not in composites:
                # add  new composite
                composites[name] = Composite(len(composites), name)
            try:
                # set attribute
                composites[name].config(attr, c_val, size)
            except RuntimeError as err:
                raise RuntimeError(
                    "syntax error in composite config value at '{}':\n{}"
                    .format(name, err))
        if add_swap:
            # add any useful swapped targets
            add_swapped_targets(composites)
        return composites

    def targets(composites):
        """ return a list of all composites that are not intermediate
        """
        result = []
        for c_name, c in composites.items():
            if not c.inter:
                result.append(c)
        return sorted(result, key=lambda c: c.order)

    def intermediates(composites):
        """ return a list of all composites that are intermediate
        """
        result = []
        for c_name, c in composites.items():
            if c.inter:
                result.append(c)
        return sorted(result, key=lambda c: c.order)


class Composite:

    def __init__(self, order, name, a=Frame(True), b=Frame(True)):
        assert type(order) is int or order is None
        assert type(name) is str or not name
        self.name = name
        self.frame = [copy.deepcopy(a), copy.deepcopy(b)]
        self.default = [None, None]
        self.inter = False
        self.noswap = False
        self.order = order

    def str_title():
        return "Key A%s\tB%s  Name" % (Frame.str_title(), Frame.str_title())

    def __str__(self):
        return "%s A%s\tB%s  %s" % (" * " if self.A().key else "   ",
                                    self.A(), self.B(), self.name)

    def equals(self, other, treat_covered_as_invisible):
        """ compare two composites if they are looking the same
            (e.g. a rectangle with size 0x0=looks the same as one with alpha=0
            and so it is treated as equal here)
        """
        if not (self.A() == other.A() or (treat_covered_as_invisible and self.covered() and other.covered())):
            return False
        elif not (self.B() == other.B() or (self.B().invisible() and other.B().invisible())):
            return False
        return True

    def A(self):
        return self.frame[0]

    def B(self):
        return self.frame[1]

    def swap(self):
        """ swap A and B source items
        """
        if self.noswap:
            return self
        else:
            # then swap frames
            self.frame = self.frame[::-1]
            self.name = swap_name(self.name)

    def swapped(self):
        """ swap A and B source items
        """
        if self.noswap:
            return self
        else:
            # deep copy everything
            s = copy.deepcopy(self)
            # then swap frames
            s.swap()
            return s

    def key(self):
        for f in self.frame:
            if f.key:
                return True
        return False

    def config(self, attr, value, size):
        """ set value <value> from INI attribute <attr>.
            <size> is the input channel size
        """
        if attr == 'a':
            self.frame[0].rect = str2rect(value, size)
        elif attr == 'b':
            self.frame[1].rect = str2rect(value, size)
        elif attr == 'crop-a':
            self.frame[0].crop = str2crop(value, size)
        elif attr == 'crop-b':
            self.frame[1].crop = str2crop(value, size)
        elif attr == 'default-a':
            self.default[0] = value
        elif attr == 'default-b':
            self.default[1] = value
        elif attr == 'alpha-a':
            self.frame[0].alpha = str2alpha(value)
        elif attr == 'alpha-b':
            self.frame[1].alpha = str2alpha(value)
        elif attr == 'inter':
            self.inter = value
        elif attr == 'noswap':
            self.noswap = value
        self.frame[0].original_size = size
        self.frame[1].original_size = size

    def covered(self):
        """ check if below is completely covered by above
            (considers shape with cropping and transparency)
        """
        below, above = self.frame
        if below.invisible():
            return True
        if above.invisible():
            return False
        bc = below.cropped()
        ac = above.cropped()
        # return if above is (semi-)transparent or covers below completely
        return (above.alpha < 255 or
                (bc[L] >= ac[L] and
                 bc[T] >= ac[T] and
                 bc[R] <= ac[R] and
                 bc[B] <= ac[B]))


def add_swapped_targets(composites):
    result = dict()
    for c_name, c in composites.items():
        if not c.inter:
            inc = True
            for v_name, v in composites.items():
                if v.equals(c.swapped(), True) and not v.inter:
                    inc = False
                    break
            if inc:
                log.debug("adding auto-swapped target %s from %s" %
                          (swap_name(c_name), c_name))
                r = c.swapped()
                r.order = len(composites) + len(result)
                result[swap_name(c_name)] = r
    return composites.update(result)


def swap_name(name): return name[1:] if name[0] == '^' else "^" + name


def absolute(str, max):
    if str == '*':
        assert max
        # return maximum value
        return int(max)
    elif '.' in str:
        assert max
        # return absolute (Pixel) value in proportion to max
        return int(float(str) * max)
    else:
        # return absolute (Pixel) value
        return int(str)


def str2rect(str, size):
    """ read rectangle pair from string '*', 'X/Y WxH', 'X/Y', 'WxH', 'X/Y WH', 'X/Y WH' or 'XY WH'
    """
    # check for '*'
    if str == "*":
        # return overall position and size
        return [0, 0, size[X], size[Y]]

    # check for 'X/Y'
    r = re.match(r'^\s*([-.\d]+)\s*/\s*([-.\d]+)\s*$', str)
    if r:
        # return X,Y and overall size
        return [absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y]),
                size[X],
                size[Y]]
    # check for 'WxH'
    r = re.match(r'^\s*([.\d]+)\s*x\s*([.\d]+)\s*$', str)
    if r:
        # return overall pos and W,H
        return [0,
                0,
                absolute(r.group(3), size[X]),
                absolute(r.group(4), size[Y])]
    # check for 'X/Y WxH'
    r = re.match(
        r'^\s*([-.\d]+)\s*/\s*([-.\d]+)\s+([.\d]+)\s*x\s*([.\d]+)\s*$', str)
    if r:
        # return X,Y,X+W,Y+H
        return [absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y]),
                absolute(r.group(1), size[X]) + absolute(r.group(3), size[X]),
                absolute(r.group(2), size[Y]) + absolute(r.group(4), size[Y])]
    # check for 'XY WxH'
    r = re.match(r'^\s*(-?\d+.\d+)\s+([.\d]+)\s*x\s*([.\d]+)\s*$', str)
    if r:
        # return XY,XY,XY+W,XY+H
        return [absolute(r.group(1), size[X]),
                absolute(r.group(1), size[Y]),
                absolute(r.group(1), size[X]) + absolute(r.group(2), size[X]),
                absolute(r.group(1), size[Y]) + absolute(r.group(3), size[Y])]
    # check for 'X/Y WH'
    r = re.match(r'^\s*([-.\d]+)\s*/\s*([-.\d]+)\s+(\d+.\d+)\s*$', str)
    if r:
        # return X,Y,X+WH,Y+WH
        return [absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y]),
                absolute(r.group(1), size[X]) + absolute(r.group(3), size[X]),
                absolute(r.group(2), size[Y]) + absolute(r.group(3), size[Y])]
    # check for 'XY WH'
    r = re.match(r'^\s*(-?\d+.\d+)\s+(\d+.\d+)\s*$', str)
    if r:
        # return XY,XY,XY+WH,XY+WH
        return [absolute(r.group(1), size[X]),
                absolute(r.group(1), size[Y]),
                absolute(r.group(1), size[X]) + absolute(r.group(2), size[X]),
                absolute(r.group(1), size[Y]) + absolute(r.group(2), size[Y])]
    # didn't get it
    raise RuntimeError("syntax error in rectangle value '{}' "
                       "(must be either '*', 'X/Y WxH', 'X/Y', 'WxH', 'X/Y WH', 'X/Y WH' or 'XY WH' where X, Y, W, H may be int or float and XY, WH must be float)".format(str))


def str2crop(str, size):
    """ read crop values pair from string '*' or 'L/T/R/B'
    """
    # check for '*'
    if str == "*":
        # return zero borders
        return [0, 0, 0, 0]
    # check for L/T/R/B
    r = re.match(
        r'^\s*([.\d]+)\s*/\s*([.\d]+)\s*/\s*([.\d]+)\s*/\s*([.\d]+)\s*$', str)
    if r:
        return [absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y]),
                absolute(r.group(3), size[X]),
                absolute(r.group(4), size[Y])]
    # check for LR/TB
    r = re.match(
        r'^\s*([.\d]+)\s*/\s*([.\d]+)\s*$', str)
    if r:
        return [absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y]),
                absolute(r.group(1), size[X]),
                absolute(r.group(2), size[Y])]
    # check for LTRB
    r = re.match(
        r'^\s*([.\d]+)\s*$', str)
    if r:
        return [absolute(r.group(1), size[X]),
                absolute(r.group(1), size[Y]),
                absolute(r.group(1), size[X]),
                absolute(r.group(1), size[Y])]
    # didn't get it
    raise RuntimeError("syntax error in crop value '{}' "
                       "(must be either '*', 'L/T/R/B', 'LR/TB', 'LTRB' where L, T, R, B, LR/TB and LTRB must be int or float')".format(str))


def str2alpha(str):
    """ read alpha values from string as float between 0.0 and 1.0 or as int between 0 an 255
    """
    # check for floating point value
    r = re.match(
        r'^\s*([.\d]+)\s*$', str)
    if r:
        # return absolute proportional to 255

        return absolute(r.group(1), 255)
    # didn't get it
    raise RuntimeError("syntax error in alpha value '{}' "
                       "(must be float or int)".format(str))
