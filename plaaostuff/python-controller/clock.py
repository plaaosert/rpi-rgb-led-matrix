import datetime
import math
import os
import platform
import threading

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


def is_float(val):
    try:
        float(val)
        return True
    except:
        return False


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

make_webrequests = True
if "--no-webrequests" in sys.argv:
    make_webrequests = False

canvas = Canvas(Vector2(64, 64))
font = Font(path.from_root("../../fonts/6x12.bdf"))
font2 = Font(path.from_root("../../fonts/5x7.bdf"))

clock_pos = Vector2(7, 1)
clock_main_col = Colour(12, 130, 12)

day_pos = Vector2(2, 14)
clock_sub_col = Colour(0, 70, 0)

date_pos = Vector2(1, 21)

temperature_pos = Vector2(42, 21)
temperature_feel_pos = Vector2(42, 28)

temperature_cols = (
    (Colour(192, 0, 0), 30),
    (Colour(128, 128, 32), 21),
    (Colour(64, 128, 64), 12),
    (Colour(0, 64, 192), 0),
    (Colour(0, 32, 128), -10),
    (Colour(0, 0, 64), -9999999)
)

current_focused_sensor_pos = Vector2(2, 35)
focused_sensor_info_pos = Vector2(2, 46)

sensors = {}
sensor_order = []
sensor_name_lookups = {
    "temp_humidity_0": "broom closet",
    "temp_humidity_1": "bedroom",
    "temp_humidity_2": "outside"
}

testing_sensors = False
if "--test-sensors" in sys.argv:
    testing_sensors = True
    for s in sensor_name_lookups.keys():
        sensors[s] = "0|0"
        sensor_order.append(s)


current_sensor = -1
sensor_switch_timeout = 0

recorded_temperature = 0
recorded_temperature_feel = 0

record_timeout = 0

last_recorded_time = time.time()

# If using pipe, set up thread here for reading from the info pipe as well
if pipe:
    def read_pipe():
        global sensors
        with open("/home/pi/sensor_inp_pipe", "r") as f:
            while True:
                data = f.read()
                if len(data) == 0:
                    pass
                    # closed pipe
                    # return

                entries = data.split("\n")
                for entry in entries:
                    if entry:
                        origin, _, payload = entry.partition(":")
                        if origin in sensor_name_lookups:
                            part1, _, part2 = entry.partition("|")
                            print(entry, is_float(part1), is_float(part2))
                            if is_float(part1) and is_float(part2):
                                if origin not in sensors:
                                    sensor_order.append(origin)

                                sensors[origin] = payload

    threading.Thread(target=read_pipe, daemon=True).start()

try:
    while True:
        while time.time() < math.floor(last_recorded_time + 1):
            time.sleep(max(0.0, min(0.25, math.floor(last_recorded_time + 1) - time.time())))

        last_recorded_time = round(time.time())

        # 30 minutes
        # TODO put this in a different thread since it'll hang the clock
        if time.time() > record_timeout + (30 * 60) and make_webrequests:
            record_timeout = time.time()
            try:
                response = requests.get("https://wttr.in/Southampton?format=\"%t|%f\"")

                recorded_temperature, recorded_temperature_feel = (int(t) for t in response.text[1:-1].replace("°C", "").split("|"))
            except:
                pass

        cur_time = datetime.datetime.now()
        canvas.set_text(clock_pos, font, cur_time.strftime('%X'), clock_main_col)
        canvas.set_text(day_pos, font2, cur_time.strftime('%A'), clock_sub_col)
        canvas.set_text(date_pos, font2, cur_time.strftime('%x'), clock_sub_col)

        if recorded_temperature or recorded_temperature_feel:
            temp_index = 0
            temperature_col = temperature_cols[0]
            while recorded_temperature < temperature_col[1]:
                temp_index += 1
                temperature_col = temperature_cols[temp_index]

            canvas.set_text(temperature_pos, font2, "{:-3}C".format(int(round(recorded_temperature))), temperature_col[0])

            temp_index = 0
            temperature_col = temperature_cols[0]
            while recorded_temperature_feel < temperature_col[1]:
                temp_index += 1
                temperature_col = temperature_cols[temp_index]

            canvas.set_text(
                temperature_feel_pos, font2, "{:-3}C".format(int(round(recorded_temperature_feel))),
                temperature_col[0].fade_black(0.5)
            )

        sensor_switch_timeout -= 1
        if sensor_switch_timeout < 0 and len(sensor_order) > 0:
            sensor_switch_timeout = 3
            current_sensor = (current_sensor + 1) % len(sensor_order)

        if current_sensor != -1:
            if sensor_order[current_sensor]:
                canvas.set_text(
                    current_focused_sensor_pos, font2, "{:^12}".format(sensor_name_lookups[sensor_order[current_sensor]]), Colour(192, 192, 192)
                )

            data = sensors[sensor_order[current_sensor]]
            if data:
                temp, _, humid = data.partition("|")

                temp_index = 0
                temperature_col = temperature_cols[0]
                while float(temp) < temperature_col[1]:
                    temp_index += 1
                    temperature_col = temperature_cols[temp_index]

                canvas.set_text(
                    focused_sensor_info_pos, font2, "{:5}{}".format(round(float(temp), 1), "C"), temperature_col[0]
                )

                canvas.set_text(
                    focused_sensor_info_pos + Vector2(34, 0), font2, "{:4}{}".format(round(float(humid), 1) if float(humid) < 100 else 100, "%"), Colour(128, 128, 128).lerp(Colour(64, 64, 255), float(humid) / 100)
                )

        canvas.set_text(
            Vector2(1, 56), font2, "<", Colour(192, 192, 192) if current_sensor > 0 else Colour(32, 32, 32)
        )

        canvas.set_text(
            Vector2(58, 56), font2, ">", Colour(192, 192, 192) if current_sensor + 1 < len(sensor_order) else Colour(32, 32, 32)
        )

        canvas.set_text(
            Vector2(15, 56), font2, "{:3}/{:<3}".format(current_sensor + 1, len(sensor_order)), Colour(192, 192, 192)
        )

        st = canvas.update_changes(clear_last=True)

        if print_canvas:
            print("\033[1;1H" + str(canvas))

        print("\033[0mLast frame took \033[32m{:8} \033[0mseconds\r".format(round(time.time() - last_print_time, 4)), end="")
        last_print_time = time.time()

        rpi_ipc.send_prot_msg(pipe, st)

        if testing_sensors:
            for s in sensor_order:
                sensors[s] = "{}|{}".format(random.randint(-2000, 4000) / 100.0, random.randint(0, 10000) / 100.0)


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
