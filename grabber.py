#grabber - picks up and puts down the package, using 2 servos
#lift servo = turns a gear that moves the whole grabber up / down
#arm servo  = swings the RIGHT arm closed (gripping against the fixed LEFT arm) or open
#when this file loads, the grabber goes UP and OPEN - so every run starts the same way

from machine import Pin, PWM
import led

#---------- angles - find these with test_grabber.py ----------
UP_ANGLE = 0              # lift servo: grabber at the top
DOWN_ANGLE = 90           # lift servo: grabber low enough for the arms to go round the package
OPEN_ANGLE = 0            # arm servo: right arm swung open
CLOSED_ANGLE = 90         # arm servo: right arm gripping the package

#---------- speed ----------
STEP_MS = 15              # servos move 1 degree every STEP_MS - bigger = slower and gentler

class Servo:
    def __init__(self, pin, start_angle):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)                 # servos need 50 Hz
        self.angle = start_angle          # remember where it is
        self.set(start_angle)

    def set(self, angle):
        #jump straight to an angle (same maths as the course's test_servo.py: 0 deg = 1638, 270 deg = 8192)
        self.pwm.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))
        self.angle = angle

    def move_to(self, target):
        #move 1 degree at a time so it doesn't jerk the package (and the amber LED keeps flashing)
        while self.angle != target:
            if self.angle < target:
                self.set(self.angle + 1)
            else:
                self.set(self.angle - 1)
            led.wait_ms(STEP_MS)


#set up both servos - grabber starts DOWN and OPEN
lift = Servo(16, DOWN_ANGLE)
arm = Servo(17, OPEN_ANGLE)


def grab():
    #pick up the package
    arm.move_to(OPEN_ANGLE)       # make sure the arm is open
    lift.move_to(DOWN_ANGLE)      # grabber down, arms either side of the package
    arm.move_to(CLOSED_ANGLE)     # swing the right arm in to grip it
    lift.move_to(UP_ANGLE)        # lift it off the table


def release():
    #put the package down
    lift.move_to(DOWN_ANGLE)      # lower it onto the rack
    arm.move_to(OPEN_ANGLE)       # let go
    lift.move_to(UP_ANGLE)        # lift the empty grabber clear