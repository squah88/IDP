#line sensors + route following
#sensors, left to right: OL (outer left), IL (inner left), IR (inner right), OR (outer right)
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

#readings
#0 0 0 0 = either at a slot or lost the line
#0 1 1 0 = move forward
#1 1 0 0 = junction
#1 1 1 0 = junction
#0 0 1 1 = junction
#0 1 1 1 = junction
#1 1 1 1 = junction
#1 0 0 0 = off line - steer left
#0 0 0 1 = off line - steer right
#0 1 0 0 = steer left
#0 0 1 0 = steer right
#anything else = can't see line properly

#how long the line must be gone before we decide it really ended (at a rack) or we're really lost
line_end_ms = 300
#a quick wobble off the line shouldn't end the whole run
lost_limit_ms = 1500

#when we first lost the line (None = we can see it)
lost_since = None

def following_line(next_node):
    #returns "following" if still following the line, "node" if a node is detected, or "lost" if the line has been lost for too long
    global lost_since
    OL, IL, IR, OR = read_sensors()
    
    #junction: reading is 1100, 1110, 0011, 0111 or 1111 - stop and let navigation choose the next move
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

    #0100 - steer left
    elif OL == 0 and IL == 1 and IR == 0 and OR == 0:
        movement.slight_left()

    #0010 - steer right
    elif OL == 0 and IL == 0 and IR == 1 and OR == 0:
        movement.slight_right()

    #all other readings (0000, or odd ones like 1001) - we can't see the line properly
    #keep doing the last movement for a moment instead of giving up straight away
    else:
        if lost_since is None:
            lost_since = time.ticks_ms()
        gone_for = time.ticks_diff(time.ticks_ms(), lost_since) #calculate how long we've been lost for

        #at rack slots the line ends (0000) - if we expect a line end and it's been gone long enough, we've arrived
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
    return "following"

#variables for what our robot does if at nodes
forward_ms = 450                #time to move forward before spinning, in milliseconds
ignore_line_ms = 300            #amount of time we ignore the sensors at the start of a left/right spin
ignore_180_ms = 1400            #how long we ignore line for 180 turn
turn_timeout_ms = 4000          #if a turn takes longer than this, give up
search_speed = 100              #spin speed once we start looking for the new line
brake_ms = 40                   #when the turn finds the line, spin backwards this long to stop overshooting
reverse_after_turn_ms = 300     #only when turning onto the main line after leaving a slot/bay: reverse this long afterwards to avoid overshooting the next junction
u_turn_direction = "right"      #which way u-turns spin - "left" or "right" - doesnt really matter except for troubleshooting

#what the current turn is doing
turning = None          #None = not turning, otherwise "left", "right" or "u_turn"
turn_started = 0        #stores the time when the spin started
turn_stage = None       #track if moving forward or spinning
spin_dir = None         #which way we are actually spinning: "left" or "right"
reverse_after = False   #True if this turn should reverse a little at the end (set by start_turn)
left_old_line = False   #becomes True once the middle sensors have come off the old line during the spin

def spin(direction, speed):
    #spin on the spot, "left" or "right"
    if direction == "left":
        movement.spin_left(speed)
    else:
        movement.spin_right(speed)

def start_turn(direction, forward_first=True, reverse_at_end=False):
    #start a turn: "left", "right" or "u_turn" (then call update_turn() every loop until it finishes)
    #forward_first = True means drive forward for a moment first, so the wheel axle reaches the junction
    #reverse_at_end = True means reverse a little once the turn is done
    global turning, turn_stage, turn_started, left_old_line, spin_dir, reverse_after

    #not a turn - just stop
    if direction not in ("left", "right", "u_turn"):
        movement.stop()
        return

    #remember which way we are turning, and whether to reverse a little at the end
    turning = direction
    reverse_after = reverse_at_end
    left_old_line = False

    #which way to spin
    if direction == "u_turn":
        spin_dir = u_turn_direction
    else:
        spin_dir = direction

    turn_started = time.ticks_ms()

    if direction == "u_turn" or not forward_first:
        #if u-turn or told not to drive forward, start spinning
        turn_stage = "spinning"
        spin(spin_dir, 60)
    else: 
        turn_stage = "forward"
        movement.move_forward()

def update_turn():
    #returns False while turning, True when facing the new line, "failed" if it took too long
    global turning, turn_stage, turn_started, left_old_line

    #no turn is in progress
    if turning is None:
        return True

    elapsed = time.ticks_diff(time.ticks_ms(), turn_started)

    #move forward for forward_ms
    if turn_stage == "forward":
        if elapsed < forward_ms:
            movement.move_forward()
            return False

        #done driving forward - start spinning and restart timer
        turn_stage = "spinning"
        turn_started = time.ticks_ms()
        spin(spin_dir, 60)
        return False

    #set ignore time based on turn type
    if turning == "u_turn":
        ignore_ms = ignore_180_ms
    else:
        ignore_ms = ignore_line_ms

    #set speed based on how long we've been spinning
    if elapsed < ignore_ms:
        speed = 70
    else:
        speed = search_speed

    spin(spin_dir, speed)

    #if we are still in the ignore period, don't check the line sensors yet
    if elapsed < ignore_ms:
        return False

    #spinning for too long so give up
    if elapsed > turn_timeout_ms:
        movement.stop()
        turning = None
        turn_stage = None
        return "failed"

    OL, IL, IR, OR = read_sensors()

    #wait until both middle sensors are off the old line
    if not left_old_line:
        if IL == 0 and IR == 0:
            left_old_line = True
        return False

    #finish when both middle sensors are on the new line
    #(outer sensors ignored - near a junction they can also see white, eg 0111 or 1111)
    if IL == 1 and IR == 1:
        #spin the other way for a moment to stop overshooting
        if spin_dir == "left":
            spin("right", search_speed)
        else:
            spin("left", search_speed)
        led.wait_ms(brake_ms)
        movement.stop()

        #only when turning onto the main line after leaving a slot/bay, reverse a little so the sensors are back behind the next junction
        if reverse_after and reverse_after_turn_ms > 0:
            movement.move_backward()
            led.wait_ms(reverse_after_turn_ms)
            movement.stop()

        turning = None
        turn_stage = None
        movement.move_forward()
        return True

    # still turning
    return False