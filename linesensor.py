#line sensors + route following
#4 sensors in a row at the front:  [OL]   [IL][IR]   [OR]
#inner pair (IL, IR) = steering, outer pair (OL, OR) = spotting junctions
#each sensor reads 1 = white (or red), 0 = black

import led
from machine import Pin
import time
import movement

#sensor pins (GP numbers) - CHECK THESE MATCH YOUR WIRING
OL = Pin(11, Pin.IN)
IL = Pin(12, Pin.IN)
IR = Pin(13, Pin.IN)
OR = Pin(14, Pin.IN)   # NOTE: the LED in led.py must NOT also be on GP14

def read_sensors():
    #returns left to right: outer left, inner left, inner right, outer right
    return OL.value(), IL.value(), IR.value(), OR.value()

#line following code
# 0 0 0 0 = stop- something wrong ADD FIXES
# 0 1 1 0 = move forward
# 1 1 0 0 = turn left
# 1 1 1 0 = turn left
# 0 0 1 1 = turn right
# 0 1 1 1 = turn right
#note: turning functions continue until middle sensors detect line
# 1 1 1 1 = junction- decide what to do next
# 0 1 0 1 = stop- something wrong ADD FIXES
# 1 0 1 0 = stop - something wrong ADD FIXES
# 1 0 0 0 = off line- turn left to find line
# 0 0 0 1 = off line- turn right to find line
# 0 1 0 0 = turn slightly left
# 0 0 1 0 = turn slightly right
# 0 1 0 1 = stop- something wrong ADD FIXES
#create global variable turning, this is used to determine if our code should 
#continue turning, or if line has been found and can stop turning

# time to move forward before spinning, in milliseconds
# needed, as wheels need to reach turn point
FORWARD_MS = 400

# amount of time we ignore the sensors
# needed, as bot keeps stopping before meeting actual line
IGNORE_LINE_MS = 600

# remembers whether the robot is currently turning
# None = not turning; "left" or "right" = turning that way
# this means robot stops turning based on if it sees 0110
turning = None

# stores the time when the spin started
turn_started = 0

def follow_line():
    # call global variables
    global turning, turn_started
    OL, IL, IR, OR = read_sensors()

    # this code checks if we are mid turn or not
    #if we are not mid turn, carries out normal line following code
    #if we are mid turn, carries out this code
    if turning is not None:

        # calculate how many milliseconds have passed since spinning started.
        elapsed = time.ticks_diff(time.ticks_ms(), turn_started)

        # compare elapsed time with variable of how long we are ignoring line
        #this ensures we dont start stracking the line until confident it has turned enough
        if elapsed >= IGNORE_LINE_MS:

            # if 0110 sensed after ignoring line time, then we are on line
            if OL == 0 and IL == 1 and IR == 1 and OR == 0:

                # toggle the turning state and resume moving forward
                turning = None
                movement.move_forward()
                return True

        # if alignment has not been accepted, keep spinning (ie. if 0110 not sensed)
        if turning == "left":
            movement.spin_left()
        else:
            movement.spin_right()

        return True

    # NORMAL LINE FOLLOWING BELOW
    # this section runs when the robot is not already turning

    # 0110- move forward
    if OL== 0 and IL == 1 and IR == 1 and OR == 0:
        movement.move_forward()

    # 1110 or 1100- left turn
    elif OL == 1 and IL == 1 and OR == 0:

        #move forward briefly so turn happens at corner
        #occurs for however lng forward time is
        movement.move_forward()
        led.wait_ms(FORWARD_MS)

        # toggle turn direction and start timer
        turning = "left"
        turn_started = time.ticks_ms()

        # start spinning left
        movement.spin_left()

    # 0111 or 0011- turn right
    elif OL == 0 and IR == 1 and OR == 1:

        # position the wheels at the corner before spinning
        movement.move_forward()
        led.wait_ms(FORWARD_MS)

        # remember the direction and start time
        turning = "right"
        turn_started = time.ticks_ms()

        # start spinning right
        movement.spin_right()

    # 1111- junction
    elif OL == 1 and IL == 1 and IR == 1 and OR == 1:
        movement.stop()
        print("junction")

    # 1000- steer left
    elif OL == 1 and IL == 0 and IR == 0 and OR == 0:
        movement.slight_left()

    # 0001- steer right
    elif OL == 0 and IL == 0 and IR == 0 and OR == 1:
        movement.slight_right()

    # 0100- slight left
    elif OL == 0 and IL == 1 and IR == 0 and OR == 0:
        movement.slight_left()

    # 0010- sleight right
    elif OL == 0 and IL == 0 and IR == 1 and OR == 0:
        movement.slight_right()

    #all other readings- stop
    else:
        movement.stop()
        print("stop - line lost")

    # tell the main loop that it can keep calling this function
    return True

