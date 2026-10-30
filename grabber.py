#grabber picks up and puts down the package using 2 servos
#lift servo = turns a gear that moves the grabber vertically
#arm servo  = swings the right arm and the left still but might change to left

from machine import Pin, PWM
import led

#important angles
UP_ANGLE = 40              #grabber at top
DOWN_ANGLE = 180           #grabber at bottom
OPEN_ANGLE_COLLECT = 85    #grabber fully opened
OPEN_ANGLE_DROPOFF = 55    #drops parcel
CLOSED_ANGLE = 40          #grabber closed

STEP_MS = 10               #servos move 1 degree every STEP_MS - greater = slower and gentler

class Servo:
    #servo class to control the grabber and arm servos
    def __init__(self, pin, start_angle):
        self.pwm = PWM(Pin(pin))
    #grabber picks up and puts down the package using 2 servos
#lift servo = turns a gear that moves the grabber vertically
#arm servo  = swings the right arm and the left still but might change to left

from machine import Pin, PWM
import led

#important angles
UP_ANGLE = 220              #grabber at top
DOWN_ANGLE = 40           #grabber at bottom
OPEN_ANGLE_COLLECT = 40    #grabber fully opened
OPEN_ANGLE_DROPOFF = 77    #drops parcel
CLOSED_ANGLE = 97          #grabber closed

STEP_MS = 10               #servos move 1 degree every STEP_MS - greater = slower and gentler

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
            led.wait_ms(STEP_MS)

#always start with the grabber down and the arm open
lift = Servo(13, DOWN_ANGLE)
arm = Servo(15, OPEN_ANGLE_COLLECT)

def grab():
    #pick up the package
    lift.move_to(DOWN_ANGLE)
    arm.move_to(OPEN_ANGLE_COLLECT)
    arm.move_to(CLOSED_ANGLE)
    lift.move_to(UP_ANGLE)


def release():
    #put the package down
    arm.move_to(OPEN_ANGLE_DROPOFF)
    
def reset_grabber():
    #reset grabber to starting position
    arm.move_to(OPEN_ANGLE_COLLECT)
    lift.move_to(DOWN_ANGLE)
    

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
            led.wait_ms(STEP_MS)

#always start with the grabber down and the arm open
lift = Servo(13, DOWN_ANGLE)
arm = Servo(15, OPEN_ANGLE_COLLECT)

def grab():
    #pick up the package
    lift.move_to(DOWN_ANGLE)
    arm.move_to(OPEN_ANGLE_COLLECT)
    arm.move_to(CLOSED_ANGLE)
    lift.move_to(UP_ANGLE)


def release():
    #put the package down
    arm.move_to(OPEN_ANGLE_DROPOFF)
    
def reset_grabber():
    #reset grabber to starting position
    arm.move_to(OPEN_ANGLE_COLLECT)
    lift.move_to(DOWN_ANGLE)