#code for line sensor- this contains the code for the readings the line sensor is giving

import led
from machine import Pin
import time
import movement

# Assign sensor and pins- GPIO numbers
left_outer = Pin(11, Pin.IN)
middle = Pin(12, Pin.IN)
right_outer = Pin(13, Pin.IN)

#####THE ROUTE
#the robot can't tell junctions apart for now so we have to tell it what to do at each one
#actions: straight, left, right, junction_u_turn, end_u_turn, end
ROUTE = [
    "straight",        # 1.  crossroad: right-hand edge of start box
    "left",            # 2.  bottom-right corner
    "left",            # 3.  T-junction to the lower box
    "junction_u_turn", # 4.  T-junction touching the collection point
    "left",            # 5.  T-junction back on the right-hand line
    "straight",        # 6.  T-junction to the upper box
    "left",            # 7.  T-junction to the line on the left
    "end_u_turn",      # 8.  end of that line
    "right",           # 9.  T-junction back on the right-hand line
    "straight",        # 10. T-junction to the upper box
    "straight",        # 11. T-junction to the lower box
    "right",           # 12. bottom-right corner
    "straight",        # 13. crossroad: right-hand edge of start box
    "end",             # 14. start spot
]

#####TUNING NUMBERS - change these on the table
JUNCTION_CONFIRM = 3          # junction must be seen this many readings in a row (stops false alarms)
JUNCTION_COOLDOWN_MS = 500    # after a junction, ignore new junctions for this long (stops double counting)
#These should make turning more precise but will implement later
#DRIVE_PAST_MS = 800           # drive forward this long before turning, so the WHEELS are over the junction
#SPIN_SKIP_MS = 400            # 90 turns: spin this long before looking for the new line (to get off the old one)
#SPIN_SKIP_180_MS = 900        # 180 turns: same idea but longer - roughly the time a 90 spin takes
STRAIGHT_MS = 300             # drive forward this long to get past a junction we're going straight over
TURN_TIMEOUT_MS = 4000        # give up a turn if no line found after this long (safety)
LINE_END_MS = 300             # line must be gone this long before we decide it has really ended
END_MS = 800                  # at the start spot, drive forward this long then stop
LOST_LIMIT_MS = 1500          # if no sensor sees the line for this long, stop (lost)

step = 0                  # which instruction in ROUTE we're on next
junction_hits = 0         # how many readings in a row have looked like a junction
last_junction_time = 0    # when we last handled a junction
lost_since = None         # when we first lost the line (None = we can see it)

#code to read the sensors and display the readings, each reading is 0 or 1, 0=black, 1=white
def read_sensors():
    LO = left_outer.value()
    M = middle.value()
    RO = right_outer.value()

    # print readings in order
    #print("Left Outer:", LO, "Middle:", M, "Right Outer:", RO)

    return LO, M, RO

#call this when the robot starts, so it begins at the first instruction again
def reset_route():
    global step, junction_hits, last_junction_time, lost_since
    step = 0
    junction_hits = 0
    last_junction_time = time.ticks_ms()   # also makes it ignore the centre spot it starts on
    lost_since = None

#what's the next instruction on the list? (None if the list is finished)
def next_action():
    if step < len(ROUTE):
        return ROUTE[step]
    else:
        return None

#for now use these then a more precise turn later
#returns True to keep going (a timed turn can't tell if it failed, so it always says True)
def turn(direction):
    if direction == "left":
        movement.turn_90_left()
    else:
        movement.turn_90_right()
    return True
 
 
def u_turn():
    movement.rotate_180_left()
    return True

#look up the next instruction in route and do it
def handle_junction():
    #returns True to keep going, False to stop
    global step
 
    action = next_action()
 
    if action is None:
        print("Found a junction but the route is finished - stopping")
        movement.stop()
        return False
 
    if action == "end_u_turn":
        #were waiting for the line to END, so a junction here is unexpected
        #drive over it without using up the instruction
        print("Unexpected junction while waiting for the end of the line - going straight")
        movement.move_forward()
        led.wait_ms(STRAIGHT_MS)
        return True
 
    step += 1
    print("Junction", step, "->", action)
 
    if action == "straight":
        movement.move_forward()
        led.wait_ms(STRAIGHT_MS)
        return True
    elif action == "left" or action == "right":
        return turn(action)
    elif action == "junction_u_turn":
        return u_turn()
    elif action == "end":
        movement.move_forward()
        led.wait_ms(END_MS)
        movement.stop()
        print("Back at the start - route complete!")
        return False
    else:   # anything unexpected
        movement.stop()
        return False
    
# line following code- this is the main code for following a line using the line sensor readings
# L M R
# 0 1 0 = on the line -> move forward
# 1 0 0 = line is to the left -> slight left
# 0 0 1 = line is to the right -> slight right
# 1 1 0 / 0 1 1 / 1 1 1 = right / left / junction -> do the next thing in ROUTE
# 0 0 0 = can't see the line -> keep going for a moment, then end_u_turn or stop
# called once every time round the main loop. Returns True to keep going, False when it's time to stop.

#updated function to follow the line
def follow_line():
    global step, junction_hits, last_junction_time, lost_since
 
    LO, M, RO = read_sensors() #READ SENSOR VALUES
    now = time.ticks_ms()
 
    #is this a junction
    at_junction = (M == 1) and (LO == 1 or RO == 1)
    cooled_down = time.ticks_diff(now, last_junction_time) > JUNCTION_COOLDOWN_MS
 
    if at_junction and cooled_down:
        junction_hits += 1
        if junction_hits >= JUNCTION_CONFIRM:     #seen it enough times in a row so its real
            junction_hits = 0
            keep_going = handle_junction()
            last_junction_time = time.ticks_ms()
            lost_since = None
            return keep_going
        return True    #not confirmed yet so keep doing what we were doing
    junction_hits = 0  #pattern broken, start counting again
 
    #normal line following
    if M == 1:
        #middle sees the line so straight
        movement.move_forward()
        lost_since = None
 
    elif LO == 1:
        #steer left if robot drifts right
        movement.slight_left()
        lost_since = None
 
    elif RO == 1:
        #steer right if robot drifts left
        movement.slight_right()
        lost_since = None
 
    else:
        #all black so we can't see the line
        #keep doing whatever we were doing and work out how long it's been
        if lost_since is None:
            lost_since = now
        gone_for = time.ticks_diff(now, lost_since)
 
        #does the line end here
        if next_action() == "end_u_turn" and gone_for > LINE_END_MS:
            step += 1
            print("Step", step, "-> end of line, u-turn")
            keep_going = u_turn()
            last_junction_time = time.ticks_ms()
            lost_since = None
            return keep_going
 
        #otherwise its probably lost
        if gone_for > LOST_LIMIT_MS:
            movement.stop()
            print("Lost the line - stopping for safety")
            return False
 
    return True
 