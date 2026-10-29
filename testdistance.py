#distance sensor test - press Stop in Thonny, then Run this file
#prints the distance in mm every 0.3 s
#use it to find OCCUPIED_MM for states.py:
#  1. put the robot at a junction, turned to face a rack slot (where it stops before checking)
#  2. write down the reading with the slot EMPTY
#  3. put a package in the slot and write down the reading again
#  4. set OCCUPIED_MM about halfway between the two numbers

import distancesensor
import time

while True:
    print("distance:", distancesensor.read_distance(), "mm")
    time.sleep(0.3)