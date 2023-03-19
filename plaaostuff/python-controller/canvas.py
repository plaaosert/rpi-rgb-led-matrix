from enum import Enum
from typing import List, Dict, Union, Tuple

import bdfparser

from dat import Vector2
from PIL import Image


class Colour:
    black = None
    white = None
    red = None
    green = None
    blue = None

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
    def from_tuple(cls, data: Union[Tuple[int, int, int], Tuple[int, int, int, int]]):
        return cls(
            data[0],
            data[1],
            data[2]
        )

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

        return Colour(self.r + other.r, self.g + other.g, self.b + other.b, ignore_validation=True)

    def __sub__(self, other):
        Colour.check_type(other)

        return Colour(self.r - other.r, self.g - other.g, self.b - other.b, ignore_validation=True)

    def __mul__(self, other):
        if isinstance(other, Colour):
            return Colour(int(self.r * other.r), int(self.g * other.g), int(self.b * other.b), ignore_validation=True)
        else:
            return Colour(int(self.r * other), int(self.g * other), int(self.b * other), ignore_validation=True)

    def __truediv__(self, other):
        return self // other

    def __floordiv__(self, other):
        if isinstance(other, Colour):
            return Colour(int(self.r // other.r), int(self.g // other.g), int(self.b // other.b), ignore_validation=True)
        else:
            return Colour(int(self.r // other), int(self.g // other), int(self.b // other), ignore_validation=True)

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
    broken_pixels = (
        Vector2(0, 0),
        Vector2(0, 1),
        Vector2(0, 2),
        Vector2(1, 0),

        Vector2(62, 61),
        Vector2(62, 62),
        Vector2(62, 63),

        Vector2(63, 61),
        Vector2(63, 62),
        Vector2(63, 63),

        *(Vector2(x, 10) for x in range(10, 40))
    )

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

            # dropped the matrix! lol
            if self.pos in Canvas.broken_pixels:
                col = Colour(0, 0, 0)

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

            # dropped the matrix so turn off all the broken pixels if we fill
            for pixel in Canvas.broken_pixels:
                changes_string += "{},0,0,0|".format(
                    str(pixel)
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
        if not ((0 <= pos.x < self.dimensions.x) and (0 <= pos.y < self.dimensions.y)):
            return

        # isnt it crazy what boilerplate can do?
        self.changes[pos] = Canvas.Pixel(pos, col)

    def set_image(self, pos: Vector2, image_draw: Image, override_col: Union[Colour, None] = None):
        image = image_draw
        if image_draw.mode != "RGBA":
            image = image_draw.convert("RGBA")

        w, h = image.size
        for x in range(w):
            for y in range(h):
                pixelpos = pos + Vector2(x, y)
                pixelcol: Tuple[int, int, int, int] = image.getpixel((x, y))
                if pixelcol[3] > 0:
                    if override_col:
                        self.set_pixel(pixelpos, override_col)
                    else:
                        self.set_pixel(pixelpos, Colour.from_tuple(pixelcol))

    def set_text(self, pos: Vector2, font: bdfparser.Font, text: str, col: Colour):
        font_text = None
        for c in text:
            if font_text:
                font_text.concat(font.glyph(c).draw())
            else:
                font_text = font.glyph(c).draw()

        if font_text:
            im = Image.frombytes("RGBA", (font_text.width(), font_text.height()), font_text.tobytes("RGBA"))
            self.set_image(pos, im, col)

    def get_pixel(self, pos: Vector2, wrt_changes: bool = True) -> Colour:
        if not ((0 <= pos.x < self.dimensions.x) and (0 <= pos.y < self.dimensions.y)):
            return Colour.black

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
