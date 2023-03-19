import datetime
import math
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
font2 = Font(path.from_root("../../fonts/5x7.bdf"))

text_pos = Vector2(7, 1)
text_col = Colour(12, 130, 12)

text_subpos = Vector2(15, 24)
text_subcol = Colour(0, 70, 0)

text_subsubpos = Vector2(15, 15)

last_recorded_time = time.time()
try:
    while True:
        while time.time() < math.floor(last_recorded_time + 1):
            time.sleep(0.1)

        last_recorded_time = round(time.time())

        cur_time = datetime.datetime.now()
        canvas.set_text(text_pos, font, cur_time.strftime('%X'), text_col)
        canvas.set_text(text_subpos, font2, cur_time.strftime('%x'), text_subcol)
        canvas.set_text(text_subsubpos, font2, cur_time.strftime('%A'), text_subcol)

        st = canvas.update_changes(clear_last=True)

        if print_canvas:
            print("\033[1;1H" + str(canvas))

        rpi_ipc.send_prot_msg(pipe, st)

except KeyboardInterrupt:
    print("\033[1;1HInterrupted. Clearing screen and exiting...\n")
    if pipe:
        pipe.write("CLEAR")
        pipe.flush()
