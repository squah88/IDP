#move the LIFT J36 - GP13
#####ON THONNY ITS ON GRABTEST.PY#####

from machine import Pin, PWM
import time

START = 135        # where the servo is NOW (= the TARGET from your last run)
TARGET = 25          # the angle to move to (0-270)
STEP_MS = 50        # wait between each 1 degree step - bigger = slower

def set_angle(angle):
    # 0 deg = 1638, 270 deg = 8192 (same maths as grabber.py)
    servo.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))

servo = PWM(Pin(13))
servo.freq(50)

angle = START                 # start from where it is now
set_angle(angle)              # hold it there
print("Starting at", angle, "- moving to", TARGET)

#move 1 degree at a time
while angle != TARGET:
    if angle < TARGET:
        angle = angle + 1
    else:
        angle = angle - 1
    set_angle(angle)
    time.sleep_ms(STEP_MS)

print("Done - servo at", angle)
