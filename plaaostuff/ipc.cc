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
  char text[PIPE_BUF];
  printf("entered read_loop\n");
  
  int running = 1;

	while (running && !interrupt_received) {
		fd = open("/home/pi/scrimblopipe", O_RDONLY);
    printf("fd: %d\n", fd);

		while ((len = read(fd, buf, PIPE_BUF)) > 0 && !interrupt_received && running) {
      for (size_t i=0; i<len; i++) {
        text[i] = buf[i];
      }
      text[len] = '\0';

      if (strcmp(text, "EXIT") == 0) {
        running = 0;
        break;
      }

      std::string s(text);
      std::string delimiter = "|";
      std::string subdelimiter = ",";

      //printf("str: %s\n", s.c_str());

      bool consumed_token = true;
      while (consumed_token) {
        consumed_token = false;
        bool need_to_parse = true;

        std::string token;
        if (s.find(delimiter) == std::string::npos) {
          token = s;
        }
        else {
          token = s.substr(0, s.find(delimiter));
        }

        if (strcmp(token.c_str(), "EXIT") == 0) {
          running = 0;
          break;
        }

        if (strcmp(token.c_str(), "CLEAR") == 0) {
          canvas->Clear();
          need_to_parse = false;
        }

        if (need_to_parse) {
          int values[5];
          bool worked = true;
          bool filling = false;
          for (int i=0; i<5; i++) {
            std::string subtoken = token.substr(0, token.find(subdelimiter));

            //printf("token;    %s\nsubtoken; %s\n", token.c_str(), subtoken.c_str());
            int v = 0;
            try {
              if (strcmp(subtoken.c_str(), "FILL") == 0) {
                filling = true;
              } else {
                v = stoi(subtoken);
              }
            } catch (std::exception &err) {
              worked = false;
              break;
            }
            values[i] = v;

            if (token.find(subdelimiter) == std::string::npos) {
              break;
            }
            else {
              token.erase(0, token.find(subdelimiter) + subdelimiter.length());
            }
          }

          if (worked) {
            if (filling) {
              canvas->Fill(values[2], values[3], values[4]);
            } else {
              canvas->SetPixel(values[0], values[1], values[2], values[3], values[4]);
            }

            if (s.find(delimiter) == std::string::npos) {
              break;
            }
            else {
              s.erase(0, s.find(delimiter) + delimiter.length());
            }
            consumed_token = true;

            //printf("remaining (%d): %s\n", s.length(), s.c_str());
          } else {
            break;
          }
        }
      }
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
  defaults.rows = 64;
  defaults.cols = 64;
  defaults.chain_length = 1;
  defaults.parallel = 1;
  defaults.show_refresh_rate = false;
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
