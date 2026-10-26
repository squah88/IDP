#grabber - picks up and puts down the package, using 2 servos
#lift servo = turns a gear that moves the whole grabber up / down
#arm servo  = swings the RIGHT arm closed (gripping against the fixed LEFT arm) or open
#when this file loads, the grabber goes DOWN and OPEN - so every run starts the same way

from machine import Pin, PWM
import led

#---------- pins - the servos plug into the board's servo connectors ----------
#J35 is wired to GP15, J36 is wired to GP13
#if the WRONG servo moves when you test, just swap these two numbers
LIFT_PIN = 13             # lift servo in J36
ARM_PIN = 15              # arm servo in J35

#---------- angles - find these with testgrabber.py ----------
UP_ANGLE = 0              # lift servo: grabber at the top
DOWN_ANGLE = 135          # lift servo: grabber low enough for the arms to go round the package - TODO: re-check with grabtest.py
OPEN_ANGLE = 135          # arm servo: right arm swung open
CLOSED_ANGLE = 100        # arm servo: right arm gripping the package

#---------- speed ----------
STEP_MS = 60              # servos move 1 degree every STEP_MS - bigger = slower and gentler

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
#lift = Servo(LIFT_PIN, DOWN_ANGLE)
#arm = Servo(ARM_PIN, OPEN_ANGLE)
#UNHASH THE PREVIOUS 2 LINES WHEN FINISHED WITH TESTING AND RUNNING MAIN.PY

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
