#!/usr/bin/env python3
# for debug logging
import logging
# for cloning objects
import copy
from typing import Optional

# substitute array coordinate mappings fer better reading
X, Y = 0, 1
L, T, R, B = 0, 1, 2, 3

log = logging.getLogger('Frame')


class Frame:
    rect: list[float]
    crop: list[float]
    alpha: int
    original_size: list[float]
    key: bool
    zorder: Optional[int]

    def __init__(self,
                 key: bool = False,
                 alpha: int = 255,
                 zorder: Optional[int] = None,
                 rect: list[float] = [0, 0, 0, 0],
                 crop: list[float] = [0, 0, 0, 0]):
        self.rect = rect
        self.crop = crop
        self.alpha = alpha
        self.original_size = [0.0, 0.0]
        self.key = key
        self.zorder = zorder

    def __repr__(self) -> str:
        z = [round(x, 1) for x in self.zoom]
        return ("{0.rect} {0.crop} {0.alpha} {1}").format(self, z)

    @staticmethod
    def str_title() -> str:
        return "(   L,   T     R,   B alpha  LCRP,TCRP,RCRP,BCRP  XZOM,YZOM,  Z)"

    def __str__(self) -> str:
        return ("(%4d,%4d  %4d,%4d  %4d  %4d,%4d,%4d,%4d  %1.2f,%1.2f, %2d)" %
                tuple(self.rect + [self.alpha] + self.crop + self.zoom() + [self.zorder if self.zorder is not None else -1]))

    def __eq__(self, other: object) -> bool:
        # do NOT compare zoom
        return self.rect == other.rect and self.crop == other.crop and self.alpha == other.alpha

    def zoomx(self) -> float:
        """ calculate x-zoom factor from relation between given size and
            width of rect in all channels
        """
        if self.crop != [0, 0, 0, 0]:
            return (self.rect[R] - self.rect[L]) / self.original_size[X]
        return 0.0

    def zoomy(self) -> float:
        """ calculate zoom factors from relation between given size and
            width and height of rect in all channels
        """
        if self.crop != [0, 0, 0, 0]:
            return (self.rect[B] - self.rect[T]) / self.original_size[Y]
        return 0.0


    def zoom(self) -> list[float]:
        """ calculate zoom factors from relation between given size and
            width and height of rect in all channels
        """
        return [self.zoomx(), self.zoomy()]

    def cropped(self) -> list[float]:
        if not self.rect:
            return None
        return [self.rect[L] + self.crop[L] * self.zoomx(),
                self.rect[T] + self.crop[T] * self.zoomy(),
                self.rect[R] - self.crop[R] * self.zoomx(),
                self.rect[B] - self.crop[B] * self.zoomy()]

    def corner(self, ix: int, iy: int) -> list[float]: return [self.rect[ix], self.rect[iy]]

    def left(self) -> float: return self.rect[L]

    def top(self) -> float: return self.rect[T]

    def width(self) -> float: return self.rect[R] - self.rect[L]

    def height(self) -> float: return self.rect[B] - self.rect[T]

    def float_alpha(self) -> float:
        return float(self.alpha) / 255.0

    def size(self) -> tuple[float, float]:
        return self.width(), self.height()

    def invisible(self) -> bool:
        return (self.rect is None or
                self.rect[R] == self.rect[L] or
                self.rect[T] == self.rect[B] or
                self.alpha == 0)

    def mirrored(self) -> 'Frame':
        # deep copy everything
        f = self.duplicate()
        # then mirror frame
        f.rect[L], f.rect[R] = f.original_size[X] - f.rect[R], f.original_size[X] - f.rect[L]
        return f

    def duplicate(self) -> 'Frame':
        return copy.deepcopy(self)
