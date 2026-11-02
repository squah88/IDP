#line sensors + route following
#inner pair (IL, IR) = steering, outer pair (OL, OR) = spotting junctions
#each sensor reads 1 = white, 0 = black

import led
from machine import Pin
import time
from mapping import line_end_nodes
import movement

#sensor pins
OL = Pin(18, Pin.IN)
IL = Pin(19, Pin.IN)
IR = Pin(20, Pin.IN)
OR = Pin(21, Pin.IN)

def read_sensors():
    #returns left to right: outer left, inner left, inner right, outer right
    return OL.value(), IL.value(), IR.value(), OR.value()

#line following code
# 0 0 0 0 = likely drop off zone point, check if it is in list of drop off zones then act
# 0 1 1 0 = move forward
# 1 1 0 0 = return our node and execute move
# 1 1 1 0 = return our node and execute move
# 0 0 1 1 = return our node and execute move
# 0 1 1 1 = return our node and execute move
# 1 1 1 1 = junction - decide what to do next
# 0 1 0 1 = stop - something wrong
# 1 0 1 0 = stop - something wrong
# 0 1 0 1 = stop - something wrong
# 1 0 1 0 = stop - something wrong
# 1 1 0 1 = stop - something wrong
# 1 0 1 1 = stop - something wrong
# 1 0 0 0 = off line - turn left to find line
# 0 0 0 1 = off line - turn right to find line
# 0 1 0 0 = turn slightly left
# 0 0 1 0 = turn slightly right

#how long the line must be gone before we decide it really ended (at a rack) or we're really lost
#a quick wobble off the line shouldn't end the whole run
line_end_ms = 300
lost_limit_ms = 1500

#when we first lost the line (None = we can see it)
lost_since = None

def following_line(next_node):
    #call global variables
    global lost_since
    OL, IL, IR, OR = read_sensors()
    

    #first find if a node is detected, this is when 1100, 1110, 0011, 0111 or 1111
    #if we are at a node, stop and return node and let navigation choose next move
    if (OL == 1 and IL == 1) or (IR == 1 and OR == 1):
        movement.stop()
        lost_since = None
        return "node"

    #0110 - move forward
    elif OL== 0 and IL == 1 and IR == 1 and OR == 0:
        movement.move_forward()

    #1000 - steer left
    elif OL == 1 and IL == 0 and IR == 0 and OR == 0:
        movement.slight_left()

    #0001- steer right
    elif OL == 0 and IL == 0 and IR == 0 and OR == 1:
        movement.slight_right()

    #0100 - slight left
    elif OL == 0 and IL == 1 and IR == 0 and OR == 0:
        movement.slight_left()

    #0010 - slight right
    elif OL == 0 and IL == 0 and IR == 1 and OR == 0:
        movement.slight_right()

    #all other readings (0000, or odd ones like 1001) - we can't see the line properly
    #keep doing the last movement for a moment instead of giving up straight away
    else:
        if lost_since is None:
            lost_since = time.ticks_ms()
        gone_for = time.ticks_diff(time.ticks_ms(), lost_since) #calculate how long we've been lost for

        #at drop off points the line ends (0000) - if we expect a line end and it's been gone long enough, we've arrived
        if next_node in line_end_nodes and OL == 0 and IL == 0 and IR == 0 and OR == 0 and gone_for > line_end_ms:
            movement.stop()
            lost_since = None
            return "node"

        #gone for too long - really lost
        if gone_for > lost_limit_ms:
            movement.stop()
            lost_since = None
            return "lost"

        return "following"

    #we can see the line, so we're not lost
    lost_since = None

    #tell the main loop that it can keep calling this function
    return "following"

#variables for what our robot does if at nodes
forward_ms = 450 #time to move forward before spinning, in milliseconds
ignore_line_ms = 300 # amount of time we ignore the sensors at the start of a left/right spin
ignore_180_ms = 1400 #how long we ignore line for 180 turn
turn_timeout_ms = 4000  #if a turn takes longer than this, give up
search_speed = 100 #spin speed once we start looking for the new line
brake_ms = 40 #when the turn finds the line, spin backwards this long to stop overshooting
u_turn_direction = "right" #which way U-turns spin - "left" or "right" - doesnt really matter except for troubleshooting

#variables to remember whether the robot is currently turning or not
turning = None #None = not turning; "left" or "right" = turning that way
turn_started = 0 #stores the time when the spin started
turn_stage = None #track if moving forward or spinning
spin_dir = None #which way we are actually spinning: "left" or "right"

#becomes True once the middle sensors have come off the old line during the spin so the the agv doesnt end up back on the old line
left_old_line = False

def spin(direction, speed):
    #spin on the spot, "left" or "right"
    if direction == "left":
        movement.spin_left(speed)
    else:
        movement.spin_right(speed)

def start_turn(direction, forward_first=True):
    #start a turn, either left, right or u_turn
    #forward_first = True means drive forward for a moment before spinning to get the wheels axle to the corner
    #forward_first = False means spin immediately without moving forward first
    global turning, turn_stage, turn_started, left_old_line, spin_dir #global variables to remember what we are doing

    #if the direction is not a turn then stop movement
    if direction not in ("left", "right", "u_turn"):
        movement.stop()
        return

    #remember which way we are turning
    turning = direction
    left_old_line = False     #haven't left the old line yet

    #which way to spin
    if direction == "u_turn":
        spin_dir = u_turn_direction
    else:
        spin_dir = direction
    #record the time when the turn started, so we can ignore the line for a moment if the sensors see it again during the spin
    turn_started = time.ticks_ms()

    if direction == "u_turn" or not forward_first:
        #if u turn or told not to drive forward, start spinning
        turn_stage = "spinning"
        spin(spin_dir, 60)

    else: 
        turn_stage = "forward"
        movement.move_forward()

#this if for figuring out when turn is complete
def update_turn():
    global turning, turn_stage, turn_started, left_old_line

    #no turn is in progress, just return
    if turning is None:
        return True

    #calculate the time that has elapseed from us starting timer in start turn and current time
    elapsed = time.ticks_diff(time.ticks_ms(), turn_started)

    #first, move forward for forward_ms
    if turn_stage == "forward":
        if elapsed < forward_ms:
            movement.move_forward()
            return False

        #once forward completed for set amount of time, change turning stage to spinning
        turn_stage = "spinning"
        #restart timer for start of spin
        turn_started = time.ticks_ms()

    #set turning directions, this only begins if just finished moving forward, otherwise goes to next if function, where it immediatley starts spinning without forward
        spin(spin_dir, 60)
        return False

    #set ignore time based on turn type
    if turning == "u_turn":
        ignore_ms = ignore_180_ms
    else:
        ignore_ms = ignore_line_ms

    #keep spinning full speed while ignoring the line then slower while looking for it to stop overshooting
    if elapsed < ignore_ms:
        speed = 70
    else:
        speed = search_speed

    spin(spin_dir, speed)

    #do not accept the old line before ignore time
    if elapsed < ignore_ms:
        return False

    #spinning for too long so give up
    if elapsed > turn_timeout_ms:
        movement.stop()
        turning = None
        turn_stage = None
        return "failed"

    OL, IL, IR, OR = read_sensors()

    #step 1: wait until both middle sensors are off the old line
    if not left_old_line:
        if IL == 0 and IR == 0:
            left_old_line = True
        return False

    #step 2: finish when both middle sensors are on the new line
    #(outer sensors ignored - near a junction they can also see white, eg 0111 or 1111)
    if IL == 1 and IR == 1:
        #spin the other way for a moment to stop overshooting
        if spin_dir == "left":
            spin("right", search_speed)
        else:
            spin("left", search_speed)
        led.wait_ms(brake_ms)
        movement.stop()

        turning = None
        turn_stage = None
        movement.move_forward()
        return True

    # still turning, repeat function
    return False

