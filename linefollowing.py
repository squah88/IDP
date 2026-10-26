#line sensors + route following
#4 sensors in a row at the front:  [OL]   [IL][IR]   [OR]
#inner pair (IL, IR) = steering, outer pair (OL, OR) = spotting junctions
#each sensor reads 1 = white (or red), 0 = black

import led
from machine import Pin
import time
from mapping import line_end_nodes
import movement

#sensor pins (GP numbers)
OL = Pin(11, Pin.IN)
IL = Pin(12, Pin.IN)
IR = Pin(13, Pin.IN)
OR = Pin(14, Pin.IN)

def read_sensors():
    #returns left to right: outer left, inner left, inner right, outer right
    return OL.value(), IL.value(), IR.value(), OR.value()

#line following code
# 0 0 0 0 = slikely drop off zone point, chekc if it is in list of drop off zones then act
# 0 1 1 0 = move forward
# 1 1 0 0 = return our node and execute move
# 1 1 1 0 = return our node and execute move
# 0 0 1 1 = return our node and execute move
# 0 1 1 1 = return our node and execute move
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

#how long the line must be gone before we decide it really ended (at a rack) or we're really lost
#a quick wobble off the line shouldn't end the whole run
LINE_END_MS = 300
LOST_LIMIT_MS = 1500

#when we first lost the line (None = we can see it)
lost_since = None

def following_line(next_node):
    #call global variables
    global lost_since
    OL, IL, IR, OR = read_sensors()

    #first find if a node is detected, this is when 1100, 1110, 0011, 0111 or if junction 1111
    #if we are at node let navigation choose move, node is taking by our code in navigation to figure out next step
    if (OL == 1 and IL == 1) or (IR == 1 and OR == 1):
        movement.stop()
        lost_since = None
        return "node"

    # 0110- move forward
    elif OL== 0 and IL == 1 and IR == 1 and OR == 0:
        movement.move_forward()

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

    #all other readings (0000, or odd ones like 1001) - we can't see the line properly
    #keep doing the last movement for a moment instead of giving up straight away
    else:
        if lost_since is None:
            lost_since = time.ticks_ms()
        gone_for = time.ticks_diff(time.ticks_ms(), lost_since)

        #at drop off points the line ends (0000) - if we expect a line end and it's been gone long enough, we've arrived
        if next_node in line_end_nodes and OL == 0 and IL == 0 and IR == 0 and OR == 0 and gone_for > LINE_END_MS:
            movement.stop()
            lost_since = None
            return "node"

        #gone for too long - really lost
        if gone_for > LOST_LIMIT_MS:
            movement.stop()
            lost_since = None
            return "lost"

        return "following"

    #we can see the line, so we're not lost
    lost_since = None

# tell the main loop that it can keep calling this function
    return "following"


#now code for what our robot does if at nodes
# time to move forward before spinning, in milliseconds
# needed, as wheels need to reach turn point
FORWARD_MS = 400

# amount of time we ignore the sensors
# needed, as bot keeps stopping before meeting actual line
IGNORE_LINE_MS = 600

# how long we idgnore line for 180 turn
IGNORE_180_MS = 1200

# if a turn takes longer than this, give up (stops it spinning forever)
TURN_TIMEOUT_MS = 6000

# remembers whether the robot is currently turning
# None = not turning; "left" or "right" = turning that way
# this means robot stops turning based on if it sees 0110
turning = None

# stores the time when the spin started
turn_started = 0

# trackr if moving forward or spinning
turn_stage = None

# DEBUG: the last sensor reading we printed (so we only print when it changes)
last_seen = None

#create function that turn robot
#this is important as we are implementing a timed turn as well as sensor turn
#our first funciton will just be for starting our turn, as we need to start by going forward so hweel on axel
def start_turn(direction):
    #call our global variables
    global turning, turn_stage, turn_started

    #if the direction is not a turn then stop movement
    if direction not in ("left", "right", "u_turn"):
        movement.stop()
        return

    # remember which way we are turning
    turning = direction
    print("START TURN:", direction)   # DEBUG
    #start timer from when turn starts
    # record the current time so update_turn() can measure elapsed time
    turn_started = time.ticks_ms()

    if direction == "u_turn":
        # if u turn, start a U-turn immediately, without moving forward
        turn_stage = "spinning"
        movement.spin_right()

    else:
        # For left/right turns, move forward first
        #we do this by just putting the stage of turn to forward
        #we call the motors to move forward in update turn
        # so the wheel axle reaches the corner
        turn_stage = "forward"
        movement.move_forward()

#this if for figuring out when turn is complete
#uses a timer to ignore line for set amount of time
#continues ignoring until it detects new line ie. 0110
#this menas it is on new line and can go forward
def update_turn():
    global turning, turn_stage, turn_started, last_seen

    # no turn is in progress, just return
    if turning is None:
        return True

    #calculate the time that has elapseed from us starting timer in start turn and current time
    elapsed = time.ticks_diff(time.ticks_ms(), turn_started)

    # DEBUG: print what the sensors see during the turn (only when the reading changes)
    seen = read_sensors()
    if seen != last_seen:
        print(turn_stage, elapsed, "ms  sensors:", seen)
        last_seen = seen

    # first, move forward for FORWARD_MS
    if turn_stage == "forward":
        if elapsed < FORWARD_MS:
            movement.move_forward()
            return False

        #once forward completed for set amount of time, change turning stage to spinning, as we begin turn 
        # start spinning
        turn_stage = "spinning"
        #restart timer for start of spin
        turn_started = time.ticks_ms()

    # set turning directions, this only begins if just finished moving forward, otherwise goes to next if function, where it immediatley starts spinning without forward
        if turning == "left":
            movement.spin_left()
        else:
            movement.spin_right()

        return False

    # keep spinning while checking for completion
    if turning == "left":
        movement.spin_left()
    else:
        movement.spin_right()

    # u turns need a longer initial ignoring period
    #same logic just longer ignore time
    #set how long we should ignore based on action
    if turning == "u_turn":
        ignore_ms = IGNORE_180_MS
    else:
        ignore_ms = IGNORE_LINE_MS

    # do not accept the old line before ignore time
    if elapsed < ignore_ms:
        return False

    # spinning for too long - give up and tell navigation the turn failed
    if elapsed > TURN_TIMEOUT_MS:
        movement.stop()
        turning = None
        turn_stage = None
        return "failed"

    OL, IL, IR, OR = read_sensors()

    # finish when aligned with the outgoing line
    if OL == 0 and IL == 1 and IR == 1 and OR == 0:
        turning = None
        turn_stage = None
        movement.move_forward()
        return True

    # still turning, repeat function
    return False