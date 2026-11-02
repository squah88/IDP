#distance sensor test - press Stop in Thonny, then Run this file
#prints the distance in mm every 0.3 s
#use it to find occupied_mm for states.py:
#  1. put the robot on a slot's line at the CHECK POINT (where it stops after check_drive_ms)
#  2. write down the reading with the slot EMPTY
#  3. put a package in the slot and write down the reading again
#  4. set occupied_mm about halfway between the two numbers

import distancesensor
import time

while True:
    print("distance:", distancesensor.read_distance(), "mm")
    time.sleep(0.3)