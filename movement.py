#this contains all the functions for what way the robot is turning and how it is moving
import time
from motor import Motor
motor3 = Motor(dirPin=4, PWMPin=5)  # Motor 3 is controlled from Motor Driv2 #1, which is on GP4/5
motor4 = Motor(dirPin=6, PWMPin=7)  # Motor 4 is controlled from Motor Driv2 #2, which is on GP6/7
   

def turn_left():
    motor3.Reverse()
    motor4.Forward()

def turn_right():
    motor3.Forward()
    motor4.Reverse()

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
    turn_time = 15000  # adjust this value based on your robot's turning speed

    while turn_time >0:
        motor3.Forward()
        motor4.Reverse()
        time.sleep(0.1)  # small delay to allow the motors to turn
        turn_time -= 0.1 #decrease the turn time by the delay amount

    motor3.off()
    motor4.off()

def rotate_180_left(): #same code as above, just turning other way
    turn_time = 15000  # adjust this value based on your robot's turning speed

    while turn_time>0:
        motor3.Reverse()
        motor4.Forward()
        time.sleep(0.1)  # small delay to allow the motors to turn
        turn_time -= 0.1 #decrease the turn time by the delay amount

    motor3.off()
    motor4.off()
        
    
    
