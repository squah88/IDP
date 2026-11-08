#test the ARM servo (J35 = GP15) - moves slowly from start to target
from machine import Pin, PWM
import time

start = 110         #where the arm is now
target = 100        #the angle to move to (0-270)
step_ms = 60        #wait between each 1 degree step - bigger = slower

def set_angle(angle):
    #0 deg = 1638, 270 deg = 8192
    arm.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))

arm = PWM(Pin(15))
arm.freq(50)

angle = start                 #start from where it is now
set_angle(angle)
print("Arm starting at", angle, "- moving to", target)

#move 1 degree at a time
while angle != target:
    if angle < target:
        angle = angle + 1
    else:
        angle = angle - 1
    set_angle(angle)
    time.sleep_ms(step_ms)

print("Done - arm at", angle)