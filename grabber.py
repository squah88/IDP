#grabber picks up and puts down the package using 2 servos
#lift servo (GP13, connector J36) turns a gear that moves the grabber up and down
#arm servo (GP15, connector J35) swings the grabber arm open and closed

from machine import Pin, PWM
import led

#important angles
up_angle = 220            #grabber at top
down_angle = 40           #grabber at bottom
open_angle_collect = 40   #grabber fully opened
open_angle_dropoff = 77   #drops parcel
closed_angle = 93         #grabber closed

step_ms = 10              #servos move 1 degree every step_ms (bigger = slower and gentler)

class Servo:
    #servo class to control the grabber and arm servos
    def __init__(self, pin, start_angle):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)                 #servos need to be 50Hz
        self.angle = start_angle          #remember where it is
        self.set(start_angle)

    def set(self, angle):
        #jump straight to an angle (0 deg = 1638, 270 deg = 8192)
        self.pwm.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))
        self.angle = angle

    def move_to(self, target):
        #moves slowly so the package doesnt jerk and the amber LED keeps flashing
        while self.angle != target:
            if self.angle < target:
                self.set(self.angle + 1)
            else:
                self.set(self.angle - 1)
            led.wait_ms(step_ms)

#always start with the grabber down and the arm open
lift = Servo(13, down_angle)
arm = Servo(15, open_angle_collect)

def grab():
    #pick up the package
    arm.move_to(closed_angle)
    lift.move_to(up_angle)

def release():
    #drop the package
    arm.move_to(open_angle_dropoff)
    
def reset_grabber():
    #reset grabber to starting position
    arm.move_to(open_angle_collect)
    lift.move_to(down_angle)