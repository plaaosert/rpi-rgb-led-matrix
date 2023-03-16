// -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; -*-
// Small example how to use the library.
// For more examples, look at demo-main.cc
//
// This code is public domain
// (but note, that the led-matrix library this depends on is GPL v2)

#include "led-matrix.h"
#include "graphics.h"

#include <string.h>
#include <unistd.h>
#include <math.h>
#include <stdio.h>
#include <signal.h>

#include <sys/stat.h>
#include <fcntl.h>
#include <limits.h>
#include <pthread.h>

using namespace rgb_matrix;

using rgb_matrix::RGBMatrix;
using rgb_matrix::Canvas;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

void read_loop(Canvas *canvas)
{
  canvas->Fill(0, 0, 0);
  Color color(255, 255, 0);
  Color bg_color(0, 0, 0);

  rgb_matrix::Font font;
  if (!font.LoadFont("/home/pi/fonts/4x6.bdf")) {
    fprintf(stderr, "Couldn't load font '%s'\n", "/home/pi/fonts/4x6.bdf");
    return;
  }

	int fd;
	size_t len;
	char buf[PIPE_BUF];
	while (1) {
		fd = open("/home/pi/scrimblopipe", O_RDONLY);
		while ((len = read(fd, buf, PIPE_BUF)) > 0) {
      if (strcmp(buf, "EXIT")) {
        break;
      }

      char text[len+1];
      for (size_t i=0; i<len; i++) {
        text[i] = buf[i];
      }

      text[len] = '\0';

      rgb_matrix::DrawText(canvas, font, 0, font.baseline(),
                         color, &bg_color, text, 0);
    }

		close(fd);
	}
}

static void DrawOnCanvas(Canvas *canvas) {
  /*
   * Let's create a simple animation. We use the canvas to draw
   * pixels. We wait between each step to have a slower animation.
   */
  canvas->Fill(0, 0, 255);

  int center_x = canvas->width() / 2;
  int center_y = canvas->height() / 2;
  float radius_max = canvas->width() / 2;
  float angle_step = 1.0 / 360;
  for (float a = 0, r = 0; r < radius_max; a += angle_step, r += angle_step) {
    if (interrupt_received)
      return;
    float dot_x = cos(a * 2 * M_PI) * r;
    float dot_y = sin(a * 2 * M_PI) * r;
    canvas->SetPixel(center_x + dot_x, center_y + dot_y,
                     255, 0, 0);
    usleep(1 * 1000);  // wait a little to slow down things.
  }
}

int main(int argc, char *argv[]) {
  RGBMatrix::Options defaults;
  defaults.hardware_mapping = "regular";  // or e.g. "adafruit-hat"
  defaults.rows = 32;
  defaults.chain_length = 1;
  defaults.parallel = 1;
  defaults.show_refresh_rate = true;
  Canvas *canvas = RGBMatrix::CreateFromFlags(&argc, &argv, &defaults);
  if (canvas == NULL)
    return 1;

  // It is always good to set up a signal handler to cleanly exit when we
  // receive a CTRL-C for instance. The DrawOnCanvas() routine is looking
  // for that.
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  read_loop(canvas);    // Using the canvas.

  // Animation finished. Shut down the RGB matrix.
  canvas->Clear();
  delete canvas;

  return 0;
}
