#code for line sensor- this contains the code for the readings the line sensor is giving
from multiprocessing.resource_sharer import stop

from machine import Pin
import time
import movement

# Assign sensor and pins- GPIO numbers
left_outer = Pin(2, Pin.IN)
<<<<<<< HEAD
middle = Pin(4, Pin.IN)
right_outer = Pin(5, Pin.IN)
=======
middle = Pin(3, Pin.IN)
right_outer = Pin(8, Pin.IN)
>>>>>>> 5c02eec10b52acb8522722b1e3b88f35cc2da0cb

#code to read the sensors and display the readings, each reading is 0 or 1, 0=black, 1=white
def read_sensors():
    LO = left_outer.value()
    M = middle.value()
    RO = right_outer.value()

    # print readings in order
    print("Left Outer:", LO, "Middle:", M, "Right Outer:", RO)

    return LO, M, RO

# line following code- this is the main code for following a line using the line sensor readings
# to prevent robot going off line, we need a function for every possible reading
# L M R
# 0 0 0 = stop- something wrong ADD FIXES
# 0 0 1 = turn right
# 0 1 0 = move forward
# 0 1 1 = turn right
# 1 0 0 = turn left
# 1 1 0 = turn left
# 1 0 1 = stop - something wrong ADD FIXES
# 1 1 1 = stop- something wrong ADD FIXES

def follow_line():
        LO, M, RO = read_sensors() #READ SENSOR VALUES

        # if it sees black on both sides, it moves forward
        if LO == 0 and M == 1 and RO == 0:
            movement.move_forward()

        #if it sees white on the right side, it turns right
        elif LO == 0 and M == 1 and RO == 1:
            movement.turn_right()

        #if it sees white on the left side, it turns left
        elif LO == 1 and M == 1 and RO == 0:
            movement.turn_left()

        # if it sees white on both sides, it stops
        elif LO == 1 and M == 1 and RO == 1:
            movement.stop()
            #DECIDE AFTER

        else :
            movement.stop()
        