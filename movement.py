#this contains all the functions for what way the robot is turning and how it is moving
import time
from motor import Motor
import led
motor3 = Motor(dirPin=4, PWMPin=5)  # motor 3 controlled from Motor Driv2 #1, which is on GP4/5
motor4 = Motor(dirPin=7, PWMPin=6)  # motor 4 controlled from Motor Driv2 #2, which is on GP6/7

def slight_left():
    motor3.Forward(30)
    motor4.Forward()

def slight_right():
    motor3.Forward()
    motor4.Forward(30)

#fucntions to spin left and right on spot, code for spinning until line is in line sensor
def spin_left(speed=70):
    motor3.Reverse(speed)
    motor4.Forward(speed)

def spin_right(speed=70):
    motor3.Forward(speed)
    motor4.Reverse(speed)

def move_forward():
    motor3.Forward()
    motor4.Forward()

def move_backward():
    motor3.Reverse()
    motor4.Reverse()

def stop():
    motor3.off()
    motor4.off()

#turn_90_left()
#turn_90_right()
#motor3.off()
#motor4.off()
#motor3.Forward()
#motor4.Forward()
#motor3.Reverse()
#motor4.Reverse()


