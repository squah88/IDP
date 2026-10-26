#test the ARM servo (J35 = GP15) - moves slowly from START to TARGET
#####ON THONNY ITS ON GRABTEST.PY#####
from machine import Pin, PWM
import time

START = 110         # where the arm is NOW
TARGET = 100        # the angle to move to (0-270)
STEP_MS = 60        # wait between each 1 degree step - bigger = slower

def set_angle(angle):
    # 0 deg = 1638, 270 deg = 8192 (same maths as grabber.py)
    arm.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))

arm = PWM(Pin(15))
arm.freq(50)

angle = START                 # start from where it is now
set_angle(angle)
print("Arm starting at", angle, "- moving to", TARGET)

#move 1 degree at a time
while angle != TARGET:
    if angle < TARGET:
        angle = angle + 1
    else:
        angle = angle - 1
    set_angle(angle)
    time.sleep_ms(STEP_MS)

print("Done - arm at", angle)
