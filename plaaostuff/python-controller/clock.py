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

clock_pos = Vector2(7, 1)
clock_main_col = Colour(12, 130, 12)

day_pos = Vector2(2, 14)
clock_sub_col = Colour(0, 70, 0)

date_pos = Vector2(1, 21)

temperature_pos = Vector2(42, 14)
temperature_cols = (
    (Colour.from_hex("CA054D"), 30),
    (Colour.from_hex("FA9F42"), 21),
    (Colour.from_hex("89BD9E"), 12),
    (Colour.from_hex("6290C3"), 0),
    (Colour.from_hex("496DDB"), -10),
    (Colour.from_hex("111D4A"), -9999999)
)

recorded_temperature = -20

last_recorded_time = time.time()
try:
    while True:
        while time.time() < math.floor(last_recorded_time - 1):
            time.sleep(0.1)

        last_recorded_time = round(time.time())

        cur_time = datetime.datetime.now()
        canvas.set_text(clock_pos, font, cur_time.strftime('%X'), clock_main_col)
        canvas.set_text(day_pos, font2, cur_time.strftime('%A'), clock_sub_col)
        canvas.set_text(date_pos, font2, cur_time.strftime('%x'), clock_sub_col)

        temp_index = 0
        temperature_col = temperature_cols[0]
        while recorded_temperature < temperature_col[1]:
            temp_index += 1
            temperature_col = temperature_cols[temp_index]

        canvas.set_text(temperature_pos, font2, "{:-3}C".format(int(round(recorded_temperature))), temperature_col[0])
        recorded_temperature += 1

        st = canvas.update_changes(clear_last=True)

        if print_canvas:
            print("\033[1;1H" + str(canvas))

        rpi_ipc.send_prot_msg(pipe, st)

except KeyboardInterrupt:
    print("\033[1;1HInterrupted. Clearing screen and exiting...\n")
    if pipe:
        pipe.write("CLEAR")
        pipe.flush()
