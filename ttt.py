# some of the ugliest code, copied from a jupyter notebook
# but it works
# run this on device

import time

TRAVERSE_HEIGHT = 150

from opentrons.execute import get_protocol_api
px = get_protocol_api("2.0")
tiprack = px.load_labware("opentrons_96_filtertiprack_20ul", 10)
instr = px.load_instrument('p20_single_gen2', 'left', tip_racks=[tiprack])
px.home()

hardware = instr._implementation._protocol_interface.get_hardware()

from opentrons import types
from opentrons.protocols.api_support.labware_like import LabwareLike

from opentrons.protocols.api_support.util import AxisMaxSpeeds
def move2(x, y, z, speed=80):
    hardware.move_to(
        types.Mount.LEFT,
        types.Point(x, y, z),
        critical_point=None,
        speed=speed,
        max_speeds=AxisMaxSpeeds()
    )

hardware._backend._smoothie_driver.set_use_wait(False)

from opentrons.protocol_api import labware
tiprack, target_well = labware.next_available_tip(
  instr.starting_tip, instr.tip_racks, instr.channels
)
move_to_location = target_well.top()

locx = 100
locy = 100

dx = 0
dy = 0

import time

MIN_X = 40
MAX_X = 360
MAX_Y = 320
MIN_Y = 40

doing = True
killed = False

dones = 0
notdones = 0

import threading

def worker():
  global locx, locy, dx, dy, dones, notdones

  print("worker started")

  while not killed:
    time.sleep(0.01) # 0.05, should be a function of distance, but this is fine for now
    if dx > 6:
        time.sleep(0.005)
    if dy > 6:
        time.sleep(0.005)

    if not doing:
      notdones += 1
      continue
    else: dones += 1

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

    move2(locx, locy, TRAVERSE_HEIGHT)

killed = False
t = threading.Thread(target=worker)
t.daemon = True
t.start()

from pygamepad import Gamepad
pad = Gamepad()

def a2d(a):
    if a   >  100: return 8
    elif a >  50: return 6
    elif a >  10: return 4
    elif a < -10: return -a2d(-a)
    else: return 0

def base(x):
  if 128 <= x <= 255:
    return x - 256
  return x

loxy, locy = 100, 100
move2(loxy, locy, TRAVERSE_HEIGHT)

hardware._backend._smoothie_driver.set_use_wait(False)
doing = True

playing = True
while playing:
    pad.read_gamepad(timeout=50)
    if pad.changed:
        x = base(pad.get_analogR_x())
        y = pad.get_analogR_y() - 128

        dx = a2d(x)
        dy = a2d(y)

        if pad.Y_was_released():
            doing = False
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("pickup")
            try:
                # translate in place
                tiprack, target_well = labware.next_available_tip(instr.starting_tip, instr.tip_racks, instr.channels)
                move_to_location = target_well.top()
                move_to_location._point = types.Point(move_to_location._point.x+0, move_to_location._point.y, move_to_location._point.z)
                instr.pick_up_tip(move_to_location)
            except Exception as e:
                print("error", e)
            locx, locy = 50, 320
            hardware._backend._smoothie_driver.set_use_wait(False)
            move2(locx, locy, TRAVERSE_HEIGHT)
            doing = True
        elif pad.X_was_released():
            doing = False
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("eject")
            try:
                instr.drop_tip()
            except Exception as e:
                print("error", e)
            hardware._backend._smoothie_driver.set_use_wait(False)
            doing = True
        elif pad.A_was_released():
            doing = False
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("aspirate", locx, locy, 20)
            try:
                instr.aspirate(20, types.Location(types.Point(locx, locy, 20), LabwareLike(None)))
            except Exception as e:
                print("error", e)
            hardware._backend._smoothie_driver.set_use_wait(False)
            move2(locx, locy, z=TRAVERSE_HEIGHT)
            doing = True
        elif pad.B_was_released():
            doing = False
            hardware._backend._smoothie_driver.set_use_wait(True)
            print("waiting")
            time.sleep(1)
            print("dispense", locx, locy, TRAVERSE_HEIGHT)
            try:
                instr.dispense(20, types.Location(types.Point(locx, locy, TRAVERSE_HEIGHT), LabwareLike(None)))
            except Exception as e:
                print("error", e)
            hardware._backend._smoothie_driver.set_use_wait(False)
            doing = True
