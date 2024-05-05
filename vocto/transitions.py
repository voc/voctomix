#!/usr/bin/env python3
# for debug logging
import logging
from vocto.composites import Composite, Composites, swap_name
from vocto.frame import Frame, L, R, T, B, X, Y

# for calculating square roots
import math

# for cloning objects
import copy

V = 2  # distance (velocity) index

log = logging.getLogger('Transitions')
logKeyFramesOnly = True


class Transitions:
    """transition table and interface"""

    # interpolation resolution
    HiRes = 0.001
    LoRes = 0.01
    resolution = HiRes

    def __init__(self, targets=[], fps=25):
        self.transitions = []
        self.targets = targets
        self.fps = fps

    def __str__(self):
        """write transition table into a string"""
        return "\n".join([t.name() for t in self.transitions])

    def __len__(self):
        return len(self.transitions)

    def count(self):
        """count available transition"""
        return len(self.transitions)

    def add(self, transition, frames):
        # check if a compatible transition is already in our pool
        for t in self.transitions:
            if t.begin().equals(transition.begin(), True) and t.end().equals(
                transition.end(), True
            ):
                # skip if found
                return
            elif t.begin().equals(transition.end(), True) and t.end().equals(
                transition.begin(), True
            ):
                self.transitions.append(t.reversed())
                return
        # otherwise calculate transition and add it to out pool
        transition.calculate(frames - 1)
        self.transitions.append(transition)

    def configure(self, cfg, composites, targets=None, fps=25):
        """generate all transitions configured in the INI-like configuration
        string in <cfg> by using the given <composites> and return them
        in a dictonary
        """

        def index(composite):
            for i in range(len(targets)):
                if composites[targets[i]].equals(composite, True):
                    return i
            return None

        # filter target composites from given composites
        if not targets:
            targets = Composites.targets(self, composites)
        # prepare result
        transitions = Transitions(targets, fps)

        # walk through all items within the configuration string
        for t_name, t in cfg:
            # split animation time and composite sequence from t
            time, sequence = t.split(',')
            time = int(time)
            # calculate frames needed for that animation time
            frames = fps * float(time) / 1000.0
            # split sequence list into key frames
            sequence = [x.strip().lower() for x in sequence.split('/')]
            for seq in parse_asterisk(sequence, targets):
                if "*" in sequence:
                    name = "%s(%s)" % (t_name, "/".join(seq))
                else:
                    name = t_name
                # prepare list of key frame composites
                transition = Transition(name)
                try:
                    # walk trough composite sequence
                    for c_name in seq:
                        # c_name = c_name.lower()
                        if c_name[0] == '^':
                            # find a composite with that name
                            transition.append(composites[c_name[1:]].swapped())
                        else:
                            # find a composite with that name
                            transition.append(composites[c_name])
                # log any failed find
                except KeyError as err:
                    raise RuntimeError(
                        'composite "{}" could not be found in transition {}'.format(
                            err, name
                        )
                    )
                transitions.add(transition, frames - 1)
        log.debug("Loaded %d transitions from configuration.", len(transitions))
        # return dictonary
        return transitions

    def solve(self, begin, end, flip):
        log.debug(
            "Solving transition %s(A,B) -> %s(%s)\n\t    %s\n\t    %s",
            begin.name,
            end.name,
            "B,A" if flip else "A,B",
            begin,
            end,
        )
        for transition in self.transitions:
            # try to find original transition
            if transition.begin().equals(begin, True) and transition.end().equals(
                end, True, flip
            ):
                log.debug("Solved #1 %s\n%s", transition.name(), transition)
                return transition, False
            if transition.begin().equals(begin, True, flip) and transition.end().equals(
                end, True
            ):
                log.debug("Solved #2 %s\n%s", transition.name(), transition)
                return transition, True
            # try reverse
            if transition.begin().equals(end, True) and transition.end().equals(
                begin, True, flip
            ):
                log.debug("Solved #3 %s\n%s", transition.name(), transition)
                return transition.reversed(), True
            if transition.begin().equals(end, True, flip) and transition.end().equals(
                begin, True
            ):
                log.debug("Solved #4 %s\n%s", transition.name(), transition)
                return transition.reversed(), False
        return None, False

    def travel(composites, previous=None):
        """return a list of pairs of composites along all possible transitions
        between all given composites by walking the tree of all combinations
        """
        # if there is only one composite
        if len(composites) == 1:
            # transition to itself
            return [composites[0], composites[0]]
        # if call is not from recursion
        if not previous:
            # insert random first station
            return Transitions.travel(composites, composites[0:1])
        # if maximum length has been reached
        if len(previous) == len(composites) * len(composites) + 1:
            # return ready sequence
            return previous
        # for all composites
        for a in composites:
            # check if we haven't had that combination previously
            if not is_in(previous, [previous[-1], a]):
                # try that combination
                r = Transitions.travel(composites, previous + [a])
                # return result if we are ready here
                if r:
                    return r
        # no findings
        return None


class Transition:

    def __init__(self, name, a=None, b=None):
        assert isinstance(name, str)
        self._name = name
        if a:
            # no overloaded constructors available in python m(
            if b:
                # got lists of frames in a and b with same length?
                assert len(a) == len(b)
                assert isinstance(a[0], Frame)
                assert isinstance(b[0], Frame)
                # rearrange composites
                self.composites = [Composite("...", a[i], b[i]) for i in range(len(a))]
            else:
                # if we got only one list then it must be composites
                assert isinstance(a[0], Composite)
                self.composites = a
        else:
            self.composites = []
        self.flip = None

    def __str__(self):
        def hidden(x, hidden):
            return str(x).replace(' ', '_') if hidden else str(x)

        # remember index when to flip sources A/B
        result = "\t%s = %s -> %s:\n" % (
            self.name(),
            self.begin().name,
            self.end().name,
        )
        # add table title
        result += "\tNo. %s\n" % Composite.str_title(self)
        # add composites until flipping point
        for i in range(self.frames()):
            if (not logKeyFramesOnly) or self.A(i).key:
                result += (
                    "\t%3d %s "
                    + ("B%s\tA%s" if self.flip and i >= self.flip else "A%s\tB%s")
                    + "  %s\n"
                ) % (
                    i,
                    " * " if self.A(i).key else "   ",
                    hidden(
                        self.A(i), self.A(i).invisible() or self.composites[i].covered()
                    ),
                    hidden(self.B(i), self.B(i).invisible()),
                    self.composites[i].name,
                )
        return result

    def phi(self):
        return self.begin().equals(self.end().swapped(), False)

    def name(self):
        if self.phi():
            return "Φ(" + self._name + ")"
        else:
            return self._name

    def append(self, composite):
        assert isinstance(composite, Composite)
        self.composites.append(composite)

    def frames(self):
        return len(self.composites)

    def A(self, n=None):
        if n is None:
            return [c.A() for c in self.composites]
        else:
            assert isinstance(n, int)
            return self.composites[n].A()

    def B(self, n=None):
        if n is None:
            return [c.B() for c in self.composites]
        else:
            assert isinstance(n, int)
            return self.composites[n].B()

    def Az(self, z0, z1):
        frames = []
        for i, c in enumerate(self.composites):
            if (not self.flip) or i < self.flip:
                frames.append(c.Az(z0))
            else:
                frames.append(c.Az(z1))
        return frames

    def Bz(self, z0, z1):
        frames = []
        for i, c in enumerate(self.composites):
            if (not self.flip) or i < self.flip:
                frames.append(c.Bz(z0))
            else:
                frames.append(c.Bz(z1))
        return frames

    def begin(self):
        return self.composites[0]

    def end(self):
        return self.composites[-1]

    def reversed(self):
        return Transition(self._name + "⁻¹", self.composites[::-1])

    def swapped(self):
        return Transition(swap_name(self._name), [c.swapped() for c in self.composites])

    def calculate_flip(self):
        """find the first non overlapping rectangle pair within parameters and
        return it's index
        """
        # check if a phi was applied
        if self.phi():

            # check if rectangle a and b overlap
            def overlap(a, b):
                return a[L] < b[R] and a[R] > b[L] and a[T] < b[B] and a[B] > b[T]

            # find the first non overlapping composite
            for i in range(self.frames() - 2):
                if not overlap(self.A(i).cropped(), self.B(i).cropped()):
                    return i
            # at last we need to swap at the end
            return self.frames() - 1
        # no flipping
        return None

    def calculate(self, frames, a_corner=(R, T), b_corner=(L, T)):
        """calculate a transition between the given composites which shall
        have the given amount of frames. Use a_corner of frames in A and
        b_corner of frames in B to interpolate the animation movement.
        """
        if len(self.composites) != frames:
            num_keys = len(self.keys())
            if len(self.composites) != num_keys:
                log.warning("Recalculating transition %s" % self.name())
                self.composites = self.keys()
            # calculate that transition and place it into the dictonary
            log.debug(
                "Calculating transition %s\t= %s \t(%s key frames)"
                % (self.name(), " / ".join([c.name for c in self.composites]), num_keys)
            )

            # extract two lists of frames for use with interpolate()
            a = [c.A() for c in self.composites]
            b = [c.B() for c in self.composites]
            # check if begin and end of animation are equal
            if a[-1] == a[0] and b[-1] == b[0]:
                # then swap the end composite
                a[-1], b[-1] = b[-1], a[-1]
            # generate animation
            a = interpolate(a, frames, a_corner)
            b = interpolate(b, frames, b_corner)
            composites = []
            j = 0
            for i in range(len(a)):
                if a[i].key:
                    name = self.composites[j].name
                    j += 1
                else:
                    name = "..."
                composites.append(Composite(len(composites), name, a[i], b[i]))
            self.composites = composites
            self.flip = self.calculate_flip()

    def keys(self):
        """return the indices of all key composites"""
        return [i for i in self.composites if i.key()]


def parse_asterisk(sequence, composites):
    """parses a string like '*/*' and returns all available variants with '*'
    being replaced by composite names in 'composites'.
    """
    sequences = []
    for k in range(len(sequence)):
        if sequence[k] == '*':
            for c in composites:
                sequences += parse_asterisk(
                    sequence[:k] + [c.name] + sequence[k + 1:], composites
                )
    if not sequences:
        sequences.append(sequence)
    return sequences


def frange(x, y, jump):
    """like range() but for floating point values"""
    while x < y:
        yield x
        x += jump


def bspline(points):
    """do a B - Spline interpolation between the given points
    returns interpolated points
    """
    # for generating B-Splines
    from scipy import interpolate as spi

    # for converting arrays
    import numpy as np

    # parameter check
    assert isinstance(points, np.ndarray)
    assert isinstance(points[0], np.ndarray) and len(points[0]) == 2
    assert isinstance(points[1], np.ndarray) and len(points[1]) == 2
    resolution = Transitions.resolution
    # check if we have more than two points
    if len(points) > 2:
        # do interpolation
        tck, u = spi.splprep(points.transpose(), s=0, k=2)
        unew = np.arange(0, 1.0 + resolution, resolution)
        return spi.splev(unew, tck)
    elif len(points) == 2:
        # throw points on direct line
        x, y = [], []
        for i in frange(0.0, 1.0 + resolution, resolution):
            x.append(points[0][X] + (points[1][X] - points[0][X]) * i)
            y.append(points[0][Y] + (points[1][Y] - points[0][Y]) * i)
        return [np.array(x), np.array(y)]
    else:
        return None


def find_nearest(spline, points):
    """find indices in spline which are most near to the coordinates in points"""
    # for converting arrays
    import numpy as np

    nearest = []
    for p in points:
        # calculation lamba fn
        distance = (spline[X] - p[X]) ** 2 + (spline[Y] - p[Y]) ** 2
        # get index of point with the minimum distance
        idx = np.where(distance == distance.min())
        nearest.append(idx[0][0])
    # return nearest points
    return nearest


def measure(points):
    """measure distances between every given 2D point and the first point"""
    positions = [(0, 0, 0)]
    # enumerate between all points
    for i in range(1, len(points)):
        # calculate X/Y distances
        dx = points[i][X] - points[i - 1][X]
        dy = points[i][Y] - points[i - 1][Y]
        # calculate movement speed V
        dv = math.sqrt(dx**2 + dy**2)
        # sum up to last position
        dx = positions[-1][X] + abs(dx)
        dy = positions[-1][Y] + abs(dy)
        dv = positions[-1][V] + dv
        # append to result
        positions.append((dx, dy, dv))
    # return array of distances
    return positions


def smooth(x):
    """smooth value x by using a cosinus wave (0.0 <= x <= 1.0)"""
    return (-math.cos(math.pi * x) + 1) / 2


def distribute(points, positions, begin, end, x0, x1, n):
    """from the sub set given by <points>[<begin>:<end>+1] selects <n> points
    whose distances are smoothly distributed and returns them.
    <poisitions> holds a list of distances between all <points> that will
    be used for smoothing the distribution.
    """
    # for converting arrays
    import numpy as np
    assert isinstance(points, np.ndarray)
    assert isinstance(positions, list)
    assert isinstance(begin, np.int64)
    assert isinstance(end, np.int64)
    assert isinstance(x0, float)
    assert isinstance(x1, float)
    assert isinstance(n, int)
    # calculate overall distance from begin to end
    length = positions[end - 1][V] - positions[begin][V]
    # begin result with the first point
    result = []
    # check if there is no movement
    if length == 0.0:
        for i in range(0, n):
            result.append(points[begin])
    else:
        # calculate start points
        pos0 = smooth(x0)
        pos1 = smooth(x1)
        for i in range(0, n):
            # calculate current x
            x = smooth(x0 + ((x1 - x0) / n) * i)
            # calculate distance on curve from y0 to y
            pos = (x - pos0) / (pos1 - pos0) * length + positions[begin][V]
            # find point with that distance
            for j in range(begin, end):
                if positions[j][V] >= pos:
                    # append point to result
                    result.append(points[j])
                    break
    # return result distribution
    return result


def fade(begin, end, factor):
    """return value within begin and end at < factor > (0.0..1.0)"""
    # check if we got a bunch of values to morph
    if type(begin) in [list, tuple]:
        result = []
        # call fade() for every of these values
        for i in range(len(begin)):
            result.append(fade(begin[i], end[i], factor))
    else:
        # return the resulting float
        result = begin + (end - begin) * factor
    return result


def morph(begin, end, pt, corner, factor):
    """interpolates a new frame between two given frames 'begin and 'end'
    putting the given 'corner' of the new frame's rectangle to point 'pt'.
    'factor' is the position bewteen begin (0.0) and end (1.0).
    """
    result = Frame()
    # calculate current size
    size = fade(begin.size(), end.size(), factor)
    # calculate current rectangle
    result.rect = [
        pt[X] if corner[X] is L else int(round(pt[X] - size[X])),
        pt[Y] if corner[Y] is T else int(round(pt[Y] - size[Y])),
        pt[X] if corner[X] is R else int(round(pt[X] + size[X])),
        pt[Y] if corner[Y] is B else int(round(pt[Y] + size[Y])),
    ]
    # calculate current alpha value and cropping
    result.alpha = int(round(fade(begin.alpha, end.alpha, factor)))
    result.crop = [int(round(x)) for x in fade(begin.crop, end.crop, factor)]
    # copy orignial size from begin
    result.original_size = begin.original_size
    return result


def interpolate(key_frames, num_frames, corner):
    """interpolate < num_frames > points of one corner defined by < corner >
    between the rectangles given by < key_frames >
    """
    # for converting arrays
    import numpy as np

    # get corner points defined by index_x,index_y from rectangles
    corners = np.array([i.corner(corner[X], corner[Y]) for i in key_frames])
    # interpolate between corners and get the spline points and the indexes of
    # those which are the nearest to the corner points
    spline = bspline(corners)
    # skip if we got no interpolation
    if not spline:
        return [], []
    # find indices of the corner's nearest points within the spline
    corner_indices = find_nearest(spline, corners)
    # transpose point array
    spline = np.transpose(spline)
    # calulcate number of frames between every corner
    num_frames_per_move = int(round(num_frames / (len(corner_indices) - 1)))
    # measure the spline
    positions = measure(spline)
    # fill with point animation from corner to corner
    animation = []
    for i in range(1, len(corner_indices)):
        # substitute indices of corner pair
        begin = corner_indices[i - 1]
        end = corner_indices[i]
        # calculate range of X between 0.0 and 1.0 for these corners
        _x0 = (i - 1) / (len(corner_indices) - 1)
        _x1 = i / (len(corner_indices) - 1)
        # create distribution of points between these corners
        corner_animation = distribute(
            spline, positions, begin, end, _x0, _x1, num_frames_per_move - 1
        )
        # append first rectangle from parameters
        animation.append(key_frames[i - 1])
        # cound index
        for j in range(len(corner_animation)):
            # calculate current sinus wave acceleration
            frame = morph(
                key_frames[i - 1],
                key_frames[i],
                corner_animation[j],
                corner,
                smooth(j / len(corner_animation)),
            )
            # append to resulting animation
            animation.append(frame)
    # append last rectangle from parameters
    animation.append(key_frames[-1])
    # return rectangle animation
    return animation


def is_in(sequence, part):
    """returns true if 2-item list 'part' is in list 'sequence'"""
    assert len(part) == 2
    for i in range(0, len(sequence) - 1):
        if sequence[i:i + 2] == part:
            return True
    return False


def fade_alpha(frame, alpha, frames):
    result = []
    for i in range(0, frames):
        f = frame.duplicate()
        f.alpha = fade(frame.alpha, alpha, smooth(float(i) / frames))
        result.append(f)
    return result
