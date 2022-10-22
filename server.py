# runs on Opentrons

import time

TRAVERSE_HEIGHT = 150

from opentrons.execute import get_protocol_api
px = get_protocol_api("2.0")
tiprack = px.load_labware("opentrons_96_tiprack_300ul", 10)
instr = px.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack])
px.home()

hardware = instr._implementation._protocol_interface.get_hardware()

from opentrons import types
from opentrons.protocols.api_support.labware_like import LabwareLike

from opentrons.protocols.api_support.util import AxisMaxSpeeds
def move2(x, y, z):
  hardware.move_to(
    types.Mount.RIGHT,
    types.Point(x, y, z),
    critical_point=None,
    speed=40,
    max_speeds=AxisMaxSpeeds()
  )

hardware._backend._smoothie_driver.set_use_wait(False)

import socket

HOST = "0.0.0.0"
PORT = 65432

def index_to_name(i): # OT index by index is deprecated??
  """ 0 -> A1, 1 -> B1, 2 -> C1, ..., 95 -> H12 """
  return chr(ord("A") + i % 8) + str(i // 8 + 1)

while True:
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.bind((HOST, PORT))
      print("\nlistening!\n")
      s.listen()
      conn, addr = s.accept()
      with conn:
        print(f"Connected by {addr}")
        while True:
          CMD_LENGTH = len("M:xxx,yyy,zzz")
          data = conn.recv(CMD_LENGTH)
          if not data:
            continue
          data = data.decode("utf-8")
          print("got", data)

          command = data[0]

          resp = "?"
          if command == "M":
            x, y, z = data.split(":")[1].split(",")
            x, y, z = float(x), float(y), float(z)
            move2(x, y, TRAVERSE_HEIGHT)
            resp = "M"*CMD_LENGTH
          elif command == "P":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("pickup")
            instr.pick_up_tip()
            resp = f"P:{100},{300},{TRAVERSE_HEIGHT}"
            hardware._backend._smoothie_driver.set_use_wait(False)
          elif command == "E":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("eject")
            instr.drop_tip()
            resp = f"E:{390},{330},{TRAVERSE_HEIGHT}"
            hardware._backend._smoothie_driver.set_use_wait(False)
          elif command == "A":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            x, y, z = data.split(":")[1].split(",")
            x, y, z = float(x), float(y), float(z)
            print("aspirate", x, y, z)
            instr.aspirate(100, types.Location(types.Point(x, y, 50), LabwareLike(None)))
            resp = "A" * CMD_LENGTH
            hardware._backend._smoothie_driver.set_use_wait(False)
            move2(x, y, z=TRAVERSE_HEIGHT)
          elif command == "D":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            x, y, z = data.split(":")[1].split(",")
            x, y, z = float(x), float(y), float(z)
            print("dispense", x, y, z)
            instr.dispense(100, types.Location(types.Point(x, y, TRAVERSE_HEIGHT), LabwareLike(None)))
            resp = "D" * CMD_LENGTH
            hardware._backend._smoothie_driver.set_use_wait(False)
          resp = resp.encode("utf-8")
          conn.sendall(resp)
  except ConnectionResetError:
    print("ConnectionResetError")
