import os
import platform

from bdfparser import Font
from PIL import Image
import random
import time
import sys

import path
from canvas import Colour, Canvas
from dat import Vector2
import rpi_ipc


# set up constants
print_canvas = False
if "linux" in platform.platform().lower():
    print_canvas = "--print-canvas" in sys.argv
    os.system("clear")
else:
    print_canvas = "--no-print-canvas" not in sys.argv
    os.system("cls")

pipe = None
if "--no-pipe" not in sys.argv:
    pipe = rpi_ipc.open_pipe(clear=True)

canvas = Canvas(Vector2(64, 64))
font = Font(path.from_root("../../fonts/6x12.bdf"))
test = font.glyph("h").draw().concat(font.glyph("i").draw())
im = Image.frombytes("RGBA", (test.width(), test.height()), test.tobytes("RGBA"))

positions = [Vector2(10, 10)]

speeds = [Vector2(1 - (random.random() * 2), 1 - (random.random() * 2)).normalized() * (float(random.randint(50, 150)) / 200)]

w, h = im.size
cols = [Colour(random.randint(0, 256), random.randint(0, 256), random.randint(0, 256))]
bounds_x = (0, 54)
bounds_y = (0, 53)

ticks = 0
timeout = 256

frame_time = time.time()
try:
    while True:
        while time.time() - frame_time < 1/60:
            time.sleep(0.0001)

        frame_time = time.time()

        ticks += 1
        if ticks % timeout == timeout - 1:
            ticks = 0
            timeout = max(8, int(timeout / 1.05))

            positions.append(Vector2(10, 10))
            speeds.append(Vector2(1 - (random.random() * 2), 1 - (random.random() * 2)).normalized() * (float(random.randint(50, 150)) / 200))
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
            canvas.set_image(text_pos, im, cols[index])

        st = canvas.update_changes(clear_last=True)

        if print_canvas:
            print("\033[1;1H" + str(canvas))

        rpi_ipc.send_prot_msg(pipe, st)

except KeyboardInterrupt:
    print("\033[1;1HInterrupted. Clearing screen and exiting...\n")
    if pipe:
        pipe.write("CLEAR")
        pipe.flush()
