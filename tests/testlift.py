#move the LIFT J36 - GP13

from machine import Pin, PWM
import time

start = 135        #where the servo is NOW (= the target from your last run)
target = 25        #the angle to move to (0-270)
step_ms = 50       #wait between each 1 degree step - bigger = slower

def set_angle(angle):
    #0 deg = 1638, 270 deg = 8192
    servo.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))

servo = PWM(Pin(13))
servo.freq(50)

angle = start                 #start from where it is now
set_angle(angle)              #hold it there
print("Starting at", angle, "- moving to", target)

#move 1 degree at a time
while angle != target:
    if angle < target:
        angle = angle + 1
    else:
        angle = angle - 1
    set_angle(angle)
    time.sleep_ms(step_ms)

print("Done - servo at", angle)