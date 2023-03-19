import datetime
import math
import os
import platform

import requests
from bdfparser import Font
from PIL import Image
import random
import time
import sys

import path
from canvas import Colour, Canvas
from dat import Vector2
import rpi_ipc


last_print_time = time.time()


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
col = 0
cols = (
    Colour.red,
    Colour.green,
    Colour.blue,
    Colour.black
)

try:
    while True:
        canvas.set_fill(Canvas.FILLTYPE.FILL, cols[col])

        st = canvas.update_changes(clear_last=True)

        if print_canvas:
            print("\033[1;1H" + str(canvas))

        rpi_ipc.send_prot_msg(pipe, st)

        col = (col + 1) % 4
        time.sleep(1)

except KeyboardInterrupt:
    if print_canvas:
        if "linux" in platform.platform().lower():
            os.system("clear")
        else:
            os.system("cls")

        print("\033[1;1HInterrupted. Clearing screen and exiting...\n")
    else:
        print("Interrupted. Clearing screen and exiting...\n")

    if pipe:
        pipe.write("CLEAR")
        pipe.flush()
