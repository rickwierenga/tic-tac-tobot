# runs on Opentrons

import time

TRAVERSE_HEIGHT = 150

from opentrons.execute import get_protocol_api
px = get_protocol_api("2.0")
tiprack = px.load_labware("opentrons_96_tiprack_20ul", 10) # 300
instr = px.load_instrument('p20_single_gen2', 'right', tip_racks=[tiprack]) # 20
px.home()

hardware = instr._implementation._protocol_interface.get_hardware()

from opentrons import types
from opentrons.protocols.api_support.labware_like import LabwareLike
from opentrons.protocol_api import labware

from opentrons.protocols.api_support.util import AxisMaxSpeeds
def move2(x, y, z):
  hardware.move_to(
    types.Mount.RIGHT,
    types.Point(x, y, z),
    critical_point=None,
    speed=80,
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
            try:
              # translate in place
              tiprack, target_well = labware.next_available_tip(instr.starting_tip, instr.tip_racks, instr.channels)
              move_to_location = target_well.top()
              # move_to_location._point = types.Point(move_to_location._point.x+1, move_to_location._point.y, move_to_location._point.z)
              move_to_location._point = types.Point(move_to_location._point.x+0, move_to_location._point.y, move_to_location._point.z)
              instr.pick_up_tip(move_to_location)
            except Exception as e:
              print("error", e)
            px, py = 50, 320
            resp = f"P:{px:03},{py},{TRAVERSE_HEIGHT}"
            hardware._backend._smoothie_driver.set_use_wait(False)
            move2(px, py, TRAVERSE_HEIGHT)
          elif command == "E":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("eject")
            try:
              instr.drop_tip()
            except Exception as e:
              print("error", e)
            resp = f"E:{390},{330},{TRAVERSE_HEIGHT}"
            hardware._backend._smoothie_driver.set_use_wait(False)
          elif command == "A":
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            x, y, z = data.split(":")[1].split(",")
            x, y, z = float(x), float(y), float(z)
            print("aspirate", x, y, z)
            try:
              instr.aspirate(100, types.Location(types.Point(x, y, 30), LabwareLike(None)))
            except Exception as e:
              print("error", e)
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
            try:
              instr.dispense(100, types.Location(types.Point(x, y, TRAVERSE_HEIGHT), LabwareLike(None)))
            except Exception as e:
              print("error", e)
            resp = "D" * CMD_LENGTH
            hardware._backend._smoothie_driver.set_use_wait(False)
          resp = resp.encode("utf-8")
          conn.sendall(resp)
  except (ConnectionResetError, BrokenPipeError):
    print("ConnectionResetError or BrokenPipeError")
