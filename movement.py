#this contains all the functions for what way the robot is turning and how it is moving
import time
from motor import Motor
motor3 = Motor(dirPin=4, PWMPin=5)  # motor 3 controlled from Motor Driv2 #1, which is on GP4/5
motor4 = Motor(dirPin=7, PWMPin=6)  # motor 4 controlled from Motor Driv2 #2, which is on GP6/7

def slight_left():
    motor3.Forward(30)
    motor4.Forward()

def slight_right():
    motor3.Forward()
    motor4.Forward(30)

#spin on the spot - same wheel directions as turn_90_left / turn_90_right, but no timer
#these just START the spin - linesensor.py stops it when the middle sensor finds the line
def spin_left(speed=50):
    motor3.Reverse(speed)
    motor4.Forward(speed)

def spin_right(speed=50):
    motor3.Forward(speed)
    motor4.Reverse(speed)

def turn_90_left():
    motor3.Forward()
    motor4.Forward()
    time.sleep(1)
    motor3.Reverse()
    motor4.Forward()
    time.sleep(1)
    motor3.off()
    motor4.off()

def turn_90_right():
    motor3.Forward()
    motor4.Forward()
    time.sleep(1)
    motor4.Reverse()
    motor3.Forward()
    time.sleep(1)
    motor3.off()
    motor4.off()

def move_forward():
    motor3.Forward()
    motor4.Forward()

def move_backward():
    motor3.Reverse()
    motor4.Reverse()

def stop():
    motor3.off()
    motor4.off()
    
def rotate_180_right():
    motor4.Reverse()
    motor3.Forward()
    time.sleep(2.4)
    motor3.off()
    motor4.off()

def rotate_180_left():
    motor3.Reverse()
    motor4.Forward()
    time.sleep(2.4)
    motor3.off()
    motor4.off()