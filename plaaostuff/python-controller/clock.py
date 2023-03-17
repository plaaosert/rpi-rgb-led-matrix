import math
import os
from enum import Enum
from typing import Tuple, List, Dict

from bdfparser import Font
from PIL import Image
import random
import time
import sys


class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def check_type(other):
        if not isinstance(other, Vector2):
            raise TypeError("Other element must be Vector2")

    def floor_to_intvec(self):
        return Vector2(int(self.x), int(self.y))

    def __str__(self):
        return "{},{}".format(self.x, self.y)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.x, self.y))

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __add__(self, other):
        Vector2.check_type(other)

        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        Vector2.check_type(other)

        return self + (-other)

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        else:
            return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        else:
            return Vector2(self.x / other, self.y / other)

    def __floordiv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x // other.x, self.y // other.y)
        else:
            return Vector2(self.x // other, self.y // other)

    def __abs__(self):
        return Vector2(abs(self.x), abs(self.y))

    def magnitude(self):
        return math.sqrt((self.x ** 2) + (self.y ** 2))

    def distance(self, other):
        return abs(other - self).magnitude()

    def normalized(self):
        return self / self.magnitude()


class Colour:
    def __init__(self, r: int, g: int, b: int, ignore_validation=False):
        self.initialised = False
        self.r: int = r if ignore_validation else max(0, min(255, r))
        self.g: int = g if ignore_validation else max(0, min(255, g))
        self.b: int = b if ignore_validation else max(0, min(255, b))

        self.initialised = True

    @staticmethod
    def check_type(other):
        if not isinstance(other, Colour):
            raise TypeError("Other element must be Colour")

    @classmethod
    def from_hex(cls, hex_string: str):
        num = int(hex_string.replace("#", ""), 16)
        return cls((num & 0xff0000) >> 16, (num & 0x00ff00) >> 8, (num & 0x0000ff) >> 0)

    def __str__(self):
        return "{},{},{}".format(self.r, self.g, self.b)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.r, self.g, self.b))

    def __neg__(self):
        return Colour(255 - self.r, 255 - self.g, 255 - self.b)

    def __add__(self, other):
        Colour.check_type(other)

        return Colour(self.r + other.r, self.g + other.g, self.b + other.b)

    def __sub__(self, other):
        Colour.check_type(other)

        return Colour(self.r - other.r, self.g - other.g, self.b - other.b, ignore_validation=True)

    def __mul__(self, other):
        if isinstance(other, Colour):
            return Colour(int(self.r * other.r), int(self.g * other.g), int(self.b * other.b))
        else:
            return Colour(int(self.r * other), int(self.g * other), int(self.b * other))

    def __truediv__(self, other):
        return self // other

    def __floordiv__(self, other):
        if isinstance(other, Colour):
            return Colour(int(self.r // other.r), int(self.g // other.g), int(self.b // other.b))
        else:
            return Colour(int(self.r // other), int(self.g // other), int(self.b // other))

    def lerp(self, other: "Colour", amount: float) -> "Colour":
        diff = other - self
        return self + (diff * amount)

    def fade_black(self, amount: float):
        return self.lerp(Colour.black, amount)

    def fade_white(self, amount: float):
        return self.lerp(Colour.white, amount)


Colour.black = Colour(0, 0, 0)
Colour.white = Colour(255, 255, 255)
Colour.red = Colour(255, 0, 0)
Colour.green = Colour(0, 255, 0)
Colour.blue = Colour(0, 0, 255)


class Canvas:
    class FILLTYPE(Enum):
        NONE = 0
        CLEAR = 1
        FILL = 2

    class Pixel:
        def __init__(self, pos: Vector2, col: Colour):
            self.pos = pos
            self.col = col

        def __str__(self):
            # special case; if the pixel is at (4, 35), disable the green colour channel
            # (the green led is broken here)

            col = self.col
            if self.pos == Vector2(4, 35):
                col = Colour(col.r, 0, col.b)

            return "{},{}|".format(str(self.pos), str(col))

    def __init__(self, dimensions: Vector2):
        self.dimensions = dimensions

        self.fill: Canvas.FILLTYPE = Canvas.FILLTYPE.NONE
        self.fill_col: Colour = Colour.black

        self.previous_changes: Dict[Vector2, Canvas.Pixel] = {}
        self.changes: Dict[Vector2, Canvas.Pixel] = {}

        self.current_canvas: List[List[Colour]] = [
            [Colour.black for _ in range(dimensions.y)] for __ in range(dimensions.x)
        ]

    def __str__(self):
        return "\n".join(
            "".join("\x1b[38;2;{};{};{}m##".format(
                self.current_canvas[x][y].r, self.current_canvas[x][y].g, self.current_canvas[x][y].b
            ) for x in range(self.dimensions.x))
        for y in range(self.dimensions.y)) + "\x1b[0m"

    def update_changes(self, clear_last: bool = False) -> str:
        # this function will edit the board to the new state and return a string for sending through to the pipe.

        changes_string = ""

        # first, fill
        filled = False

        if self.fill == Canvas.FILLTYPE.CLEAR:
            changes_string += "CLEAR|"
            filled = True
            self.fill_col = Colour.black

            self.current_canvas: List[List[Colour]] = [
                [Colour.black for _ in range(self.dimensions.y)] for __ in range(self.dimensions.x)
            ]

        elif self.fill == Canvas.FILLTYPE.FILL:
            changes_string += "FILL,0,{}|".format(str(self.fill_col))

            # need to insert an instruction here to turn off the green LED at (4, 35)
            changes_string += "4,35,{},0,{}|".format(
                self.fill_col.r,
                self.fill_col.b
            )

            self.current_canvas: List[List[Colour]] = [
                [self.fill_col for _ in range(self.dimensions.y)] for __ in range(self.dimensions.x)
            ]

            filled = True

        # then handle every colour change
        for change in self.changes.values():
            # if the change's colour is the same as the current board's colour,
            if change.col == self.get_pixel(change.pos, wrt_changes=False):
                # don't change anything
                pass
            else:
                changes_string += str(change)
                self.current_canvas[change.pos.x][change.pos.y] = change.col

        # if there are changes in previous_changes we haven't touched yet, clear them here
        # if we filled the screen, we know that we shouldn't touch these
        if clear_last and not filled:
            for change in self.previous_changes.values():
                # if there is a previous change which isn't in current changes
                if change.pos not in self.changes:
                    # we should set it to the last fill colour
                    # (might be this one, otherwise check the value of our last fill)
                    last_fill_col = self.fill_col

                    changes_string += str(
                        Canvas.Pixel(change.pos, last_fill_col)
                    )
                    self.current_canvas[change.pos.x][change.pos.y] = last_fill_col

        self.previous_changes = self.changes
        self.changes = {}
        return changes_string

    def set_fill(self, fill_type: "Canvas.FILLTYPE", fill_col: Colour = Colour.black):
        self.fill = fill_type
        self.fill_col = fill_col

    def set_pixel(self, pos: Vector2, col: Colour):
        # isnt it crazy what boilerplate can do?
        self.changes[pos] = Canvas.Pixel(pos, col)

    def get_pixel(self, pos: Vector2, wrt_changes: bool = True) -> Colour:
        col = self.current_canvas[pos.x][pos.y]
        if wrt_changes:
            # check for any fills
            if self.fill == Canvas.FILLTYPE.CLEAR:
                col = Colour.black
            elif self.fill == Canvas.FILLTYPE.FILL:
                col = self.fill_col

            # then check for changes (fills always happen before changes)
            if pos in self.changes:
                col = self.changes[pos].col

        return col


# set up constants
os.system("clear")

pipe = None
if "-nopipe" not in sys.argv:
    pipe = open("/home/pi/scrimblopipe", "w")

canvas = Canvas(Vector2(64, 64))
font = Font("/home/pi/ledmatrix_things/rpi-rgb-led-matrix/fonts/6x12.bdf")
test = font.glyph("h").draw().concat(font.glyph("i").draw())
im = Image.frombytes("RGB", (test.width(), test.height()), test.tobytes("RGB"))

if pipe:
    pipe.write("CLEAR")
    pipe.flush()

positions = [Vector2(10, 10)]

speeds = [Vector2(1 - (random.random() * 2), 1 - (random.random() * 2)).normalized()]

w, h = im.size
cols = [Colour(random.randint(0, 192), random.randint(64, 256), random.randint(0, 192))]
bounds_x = (0, 54)
bounds_y = (0, 53)

ticks = 0
timeout = 200

frame_time = time.time()
while True:
    while time.time() - frame_time < 1/60:
        time.sleep(0.0001)

    frame_time = time.time()

    ticks += 1
    if ticks % timeout == timeout - 1:
        ticks = 0
        timeout = int(timeout / 1.3)
        positions.append(Vector2(10, 10))
        speeds.append(Vector2(1 - (random.random() * 2), 1 - (random.random() * 2)).normalized())
        cols.append(Colour(random.randint(0, 192), random.randint(64, 256), random.randint(0, 192)))

    for index in range(len(positions)):
        pos = positions[index]
        speed = speeds[index]

        positions[index] = pos + speed
        pos = positions[index]

        if not (bounds_x[0] <= pos.x < bounds_x[1]):
            speeds[index] = speed * Vector2(-1, 1)
            pos.x = max(bounds_x[0], min(bounds_x[1], pos.x))
            cols[index] = Colour(random.randint(0, 192), random.randint(64, 256), random.randint(0, 192))

        if not (bounds_y[0] <= pos.y < bounds_y[1]):
            speeds[index] = speed * Vector2(1, -1)
            pos.y = max(bounds_y[0], min(bounds_y[1], pos.y))
            cols[index] = Colour(random.randint(0, 192), random.randint(64, 256), random.randint(0, 192))

        text_pos = pos.floor_to_intvec()
        for x in range(w):
            for y in range(h):
                pixelpos = text_pos + Vector2(x, y)
                if im.getpixel((x, y)) == (0, 0, 0):
                    canvas.set_pixel(pixelpos, cols[index])

    st = canvas.update_changes(clear_last=True)

    print("\033[1;1H" + str(canvas))

    if pipe:
        pipe.write(st)
        pipe.flush()
