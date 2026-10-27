#this contains all the functions for what way the robot is turning and how it is moving
import time
from motor import Motor
import led
#on the final chassis: motor3 = RIGHT wheel, motor4 = LEFT wheel
motor3 = Motor(dirPin=4, PWMPin=5)  # RIGHT wheel - Motor Driv2 #1, on GP4/5
motor4 = Motor(dirPin=7, PWMPin=6)  # LEFT wheel  - Motor Driv2 #2, on GP6/7


#to steer LEFT, slow the LEFT wheel (motor4)
def slight_left():
    motor3.Forward()
    motor4.Forward(30)

#to steer RIGHT, slow the RIGHT wheel (motor3)
def slight_right():
    motor3.Forward(30)
    motor4.Forward()

#fucntions to spin left and right on spot, code for spinning until line is in line sensor
#spin left = right wheel forwards, left wheel backwards
def spin_left(speed=60):
    motor4.Reverse(speed)
    motor3.Forward(speed)

#spin right = left wheel forwards, right wheel backwards
def spin_right(speed=60):
    motor4.Forward(speed)
    motor3.Reverse(speed)

def move_forward():
    motor3.Forward()
    motor4.Forward()

def move_backward():
    motor3.Reverse()
    motor4.Reverse()

def stop():
    motor3.off()
    motor4.off()
