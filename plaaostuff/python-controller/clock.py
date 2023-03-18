import datetime
import math
import os

from bdfparser import Font
from PIL import Image
import random
import time
import sys

from canvas import Colour, Canvas
from dat import Vector2
import rpi_ipc


# set up constants
os.system("clear")

pipe = None
if "--no-pipe" not in sys.argv:
    pipe = rpi_ipc.open_pipe(clear=True)

print_canvas = "--print-canvas" in sys.argv

canvas = Canvas(Vector2(64, 64))
font = Font("/home/pi/ledmatrix_things/rpi-rgb-led-matrix/fonts/6x10.bdf")
font2 = Font("/home/pi/ledmatrix_things/rpi-rgb-led-matrix/fonts/4x6.bdf")

text_pos = Vector2(5, 1)
text_col = Colour(34, 139, 34)

text_subpos = Vector2(1, 13)
text_subcol = text_col.fade_black(0.4)

text_subsubpos = Vector2(32, 13)

last_recorded_time = time.time()
try:
    while True:
        while time.time() < math.floor(last_recorded_time + 1):
            time.sleep(0.1)

        last_recorded_time = round(time.time())

        cur_time = datetime.datetime.now()
        canvas.set_text(text_pos, font, cur_time.strftime('%X'), text_col)
        canvas.set_text(text_subpos, font, cur_time.strftime('%x'), text_subcol)
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
