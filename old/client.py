import socket

from pygamepad import Gamepad

HOST = "169.254.114.119" # wired
PORT = 65432

CMD_LENGTH = len("M:xxx,yyy,zzz")

def base(x):
  if 128 <= x <= 255:
    return x - 256
  return x

locx = 100
locy = 100

dx = 0
dy = 0

import time

MIN_X = 10
MAX_X = 400
MAX_Y = 380
MIN_Y = 10

doing = True

def worker():
  global locx, locy, dx, dy

  print("worker started")

  while True:
    time.sleep(0.005) # 0.05
    print("locs", locx, locy)

    if not doing:
      print("not doing")
      continue

    if dx == dy == 0:
      continue

    locx += dx
    if locx < MIN_X:
      locx = MIN_X
    elif locx > MAX_X:
      locx = MAX_X

    locy += dy
    if locy < MIN_Y:
      locy = MIN_Y
    elif locy > MAX_Y:
      locy = MAX_Y

    s.sendall(f"M:{locx:03},{locy:03},130".encode("utf-8"))
    print("sent")

    print("receiving")
    resp = s.recv(CMD_LENGTH)
    resp = resp.decode("utf-8")
    print("got", resp)

import threading

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
  s.connect((HOST, PORT))
  s.sendall(f"M:{locx},{locy},100".encode("utf-8"))

  # start worker
  t = threading.Thread(target=worker)
  t.daemon = True
  t.start()
  print('started worker')

  # read gamepad
  def do(pad):
    global dx, dy, doing, locx, locy

    playing = True # until discard

    while playing:
      pad.read_gamepad(timeout=100)
      x = base(pad.get_analogR_x())
      y = pad.get_analogR_y() - 128

      print("device read: ", x, y)

      d = 2

      threshold = 10

      if x > threshold:
        dx = d
      elif x < -threshold:
        dx = -d
      else:
        dx = 0

      if y > threshold:
        dy = d
      elif y < -threshold:
        dy = -d
      else:
        dy = 0

      # block reading on aspiration, etc.
      if pad.Y_was_released():
        doing = False
        print("Y"*100)
        s.sendall(("P"*CMD_LENGTH).encode("utf-8"))
        while True:
          resp = s.recv(CMD_LENGTH)
          resp = resp.decode("utf-8")
          print("got", resp)
          if not resp.startswith("P"):
            continue
          resp = resp[2:]
          resp = resp.split(",")
          locx, locy = int(resp[0]), int(resp[1])
          break
        doing = True
      elif pad.X_was_released():
        doing = False
        print("X"*100)
        s.sendall(("E"*CMD_LENGTH).encode("utf-8"))
        while True:
          resp = s.recv(CMD_LENGTH)
          resp = resp.decode("utf-8")
          print("got", resp)
          if not resp.startswith("E"):
            continue
          resp = resp[2:]
          resp = resp.split(",")
          locx, locy = int(resp[0]), int(resp[1])
          break
        doing = True
        playing = False
      elif pad.A_was_released():
        doing = False
        print("A"*100)
        cmd = f"A:{locx:03},{locy:03},130".encode("utf-8")
        s.sendall(cmd)
        while True:
          resp = s.recv(CMD_LENGTH)
          resp = resp.decode("utf-8")
          print("got", resp)
          if not resp.startswith("A"):
            continue
          break
        doing = True
      elif pad.B_was_released():
        doing = False
        print("B"*100)
        cmd = f"D:{locx:03},{locy:03},130".encode("utf-8")
        s.sendall(cmd)
        while True:
          resp = s.recv(CMD_LENGTH)
          resp = resp.decode("utf-8")
          print("got", resp)
          if not resp.startswith("D"):
            continue
          break
        doing = True

  left_pad = Gamepad(serial="B018AC56") # player 1
  right_pad = Gamepad(serial="E76E66AE") # player 2
  current_player = 1

  while True:
    if current_player == 1:
      do(left_pad)
    else:
      do(right_pad)
    current_player = 1 if current_player == 2 else 2
