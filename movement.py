#this contains all the functions for what way the robot is turning and how it is moving
from motor import Motor

motor3 = Motor(dirPin=4, PWMPin=5)  # LEFT wheel  - Motor Driv2 #1, on GP4/5
motor4 = Motor(dirPin=7, PWMPin=6)  # RIGHT wheel - Motor Driv2 #2, on GP6/7
#left wheel to J40 orange red
#rght wheel to J39 orange red

#how fast the slower wheel goes when steering (0-100)
#bigger = gentler corrections, smaller = sharper corrections
steer_speed = 50

#BAY MODE - used on the short line into a collection bay
bay_mode = False
bay_speed = 75            #speed of the fast wheel in bay mode and both wheels going straight
bay_steer_speed = 30      #speed of the slow wheel when steering in bay mode

#to steer LEFT, slow the LEFT wheel (motor3)
def slight_left():
    if bay_mode:
        motor3.Forward(bay_steer_speed)
        motor4.Forward(bay_speed)
    else:
        motor3.Forward(steer_speed)
        motor4.Forward()

#to steer RIGHT, slow the RIGHT wheel (motor4)
def slight_right():
    if bay_mode:
        motor3.Forward(bay_speed)
        motor4.Forward(bay_steer_speed)
    else:
        motor3.Forward()
        motor4.Forward(steer_speed)

#functions to spin left and right on spot
def spin_left(speed=60):
    motor3.Reverse(speed)
    motor4.Forward(speed)

def spin_right(speed=60):
    motor3.Forward(speed)
    motor4.Reverse(speed)

def move_forward():
    if bay_mode:
        motor3.Forward(bay_speed)
        motor4.Forward(bay_speed)
    else:
        motor3.Forward()
        motor4.Forward()

def move_backward():
    motor3.Reverse()
    motor4.Reverse()

def stop():
    motor3.off()
    motor4.off()