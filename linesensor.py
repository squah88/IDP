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
MISSED_CORNER_MS = 150        # if the line vanishes this long when the next instruction is a turn, assume we just missed a corner
#which junction numbers (from the ROUTE comments) are CORNERS - places where the line ENDS and turns
#the missed-corner backup ONLY works at these, never at T-junctions
CORNERS = [2, 12]             # 2 and 12 = the bottom-right corner (on the way out and on the way back)
JUNCTION_COOLDOWN_MS = 500    # after a junction, ignore new junctions for this long (stops double counting)
START_IGNORE_MS = 1500        # when the route starts, ignore junctions for this long (so the centre spot isn't counted)
#sensor-based turning
DRIVE_PAST_MS = 800           # drive forward this long before a 90 turn, so the WHEELS are over the junction
SPIN_MIN_MS = 150             # always spin at least this long before looking for the line
SPIN_MIN_180_MS = 300         # same for 180 turns
SPIN_EXTRA_MS = 150           # after the middle sensor finds the line, keep spinning this long so it ends up ON the line, not at its edge
STRAIGHT_MS = 300             # drive forward this long to get past a junction we're going straight over
TURN_TIMEOUT_MS = 4000        # give up a turn if no line found after this long (safety)
LINE_END_MS = 300             # line must be gone this long before we decide it has really ended
END_MS = 800                  # at the start spot, drive forward this long then stop
LOST_LIMIT_MS = 1500          # if no sensor sees the line for this long, stop (lost)
#collection point (the red box) - red reads as 1 on all three sensors, just like white
BAR_SKIP_MS = 200             # after the T-junction, drive this long first so we don't mistake the T's bar for the box
BOX_CONFIRM = 3               # all three sensors must see red this many readings in a row
BOX_EXTRA_MS = 600              # once red is found, drive this much further before stopping (0 = stop straight away)
BOX_TIMEOUT_MS = 3000         # if we never find the red box, u-turn anyway after this long (safety)
CLEAR_BAR_MS = 0              # after the u-turn, drive this long before counting junctions again (raise if it counts the T's bar)

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
    # pretend the last junction was a bit in the FUTURE, so the cooldown lasts START_IGNORE_MS at the start
    # (ticks_add is the safe way to add to a ticks_ms time)
    last_junction_time = time.ticks_add(time.ticks_ms(), START_IGNORE_MS - JUNCTION_COOLDOWN_MS)
    lost_since = None

#what's the next instruction on the list? (None if the list is finished)
def next_action():
    if step < len(ROUTE):
        return ROUTE[step]
    else:
        return None

#spin until the middle sensor finds a line - works however fast or slow the motors are
#returns True if it found the line, False if it gave up
def spin_to_line(direction, min_ms):
    # 1. start spinning
    if direction == "left":
        movement.spin_left()
    else:
        movement.spin_right()

    # 2. always spin for a moment first
    led.wait_ms(min_ms)

    start = time.ticks_ms()

    # 3. if the middle sensor is still on something white (the old line, or the red box),
    #    keep spinning until it's OFF it - otherwise we'd "find" the line we're already on
    while middle.value() == 1:
        led.update_flash()
        if time.ticks_diff(time.ticks_ms(), start) > TURN_TIMEOUT_MS:
            movement.stop()
            print("Turn failed - never got off the old line")
            return False

    # 4. now keep spinning until the middle sensor finds the NEW line
    while middle.value() == 0:
        led.update_flash()
        if time.ticks_diff(time.ticks_ms(), start) > TURN_TIMEOUT_MS:
            movement.stop()
            print("Turn failed - couldn't find the line")
            return False

    # 5. found it - spin a tiny bit more so we end up in the middle of the line, not just its edge
    led.wait_ms(SPIN_EXTRA_MS)

    # 6. stop spinning, line following takes over from here
    movement.stop()
    return True


#90 turn at a junction
def turn(direction):
    # drive forward first so the wheels (not just the sensors) are over the junction
    movement.move_forward()
    led.wait_ms(DRIVE_PAST_MS)
    return spin_to_line(direction, SPIN_MIN_MS)


#180 turn on the spot (no driving forward first)
def u_turn():
    return spin_to_line("left", SPIN_MIN_180_MS)


#at the collection point: keep going until the sensors reach the red box, THEN u-turn
#red reads as 1 on all three sensors, so "all three see 1" = we've reached the box
def box_u_turn():
    # 1. drive a little first so the sensors get off the T-junction's bar (that's also 1 1 1)
    movement.move_forward()
    led.wait_ms(BAR_SKIP_MS)

    # 2. keep following the line until all three sensors see red
    start = time.ticks_ms()
    red_hits = 0
    while red_hits < BOX_CONFIRM:
        LO, M, RO = read_sensors()

        if LO == 1 and M == 1 and RO == 1:
            red_hits += 1          # looks like red - count it, keep driving
        else:
            red_hits = 0           # not red yet - keep following the line towards the box
            if M == 1:
                movement.move_forward()
            elif LO == 1:
                movement.slight_left()
            elif RO == 1:
                movement.slight_right()

        # safety: don't drive forever if we never find it
        if time.ticks_diff(time.ticks_ms(), start) > BOX_TIMEOUT_MS:
            print("Never found the red box - u-turning anyway")
            break

        led.wait_ms(10)   # same pace as the main loop, and keeps the LED flashing

    # 3. optionally go a tiny bit further onto the red, then stop
    if BOX_EXTRA_MS > 0:
        movement.move_forward()
        led.wait_ms(BOX_EXTRA_MS)
    movement.stop()
    print("At the red box - u-turn")

    # 4. turn round until the middle sensor finds the line behind us
    if not u_turn():
        return False

    # 5. drive forward a bit so we don't count the T's bar as the next junction on the way back
    if CLEAR_BAR_MS > 0:
        movement.move_forward()
        led.wait_ms(CLEAR_BAR_MS)
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
        return box_u_turn()     # go up to the red box first, then u-turn
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
# 1 1 0 / 0 1 1 = EITHER a junction OR just a wobble (line under two sensors) -> steer, and only
#                 count it as a junction if it lasts AND it's on the side the route is turning to
# 1 1 1 = junction (or crossroad) -> do the next thing in ROUTE
# 0 0 0 = can't see the line -> keep going for a moment, then end_u_turn or stop
# called once every time round the main loop. Returns True to keep going, False when it's time to stop.

#does this junction have a line on the side the route is about to turn to?
#a LEFT turn needs a line on the left, a RIGHT turn needs a line on the right
#this stops a wobble (e.g. 0 1 1) being mistaken for a left corner
def side_matches(LO, RO):
    action = next_action()
    if action == "left":
        return LO == 1
    elif action == "right":
        return RO == 1
    else:
        return True    # straight / u-turn / end - any junction pattern is fine


#small steering corrections to stay on the line
#returns True if any sensor can see the line, False if all three see black
def steer(LO, M, RO):
    if M == 1 and LO == 1 and RO == 0:
        movement.slight_left()     # line is under the middle AND left -> robot has drifted right
    elif M == 1 and RO == 1 and LO == 0:
        movement.slight_right()    # line is under the middle AND right -> robot has drifted left
    elif M == 1:
        movement.move_forward()    # centred (or all three on white) -> straight
    elif LO == 1:
        movement.slight_left()
    elif RO == 1:
        movement.slight_right()
    else:
        return False               # can't see the line at all
    return True


#updated function to follow the line
def follow_line():
    global step, junction_hits, last_junction_time, lost_since

    LO, M, RO = read_sensors() #READ SENSOR VALUES
    now = time.ticks_ms()

    #is this a junction - middle on the line, a side sensor on a line, AND on the side the route needs
    at_junction = (M == 1) and (LO == 1 or RO == 1) and side_matches(LO, RO)
    cooled_down = time.ticks_diff(now, last_junction_time) > JUNCTION_COOLDOWN_MS

    if at_junction and cooled_down:
        junction_hits += 1
        if junction_hits >= JUNCTION_CONFIRM:     #seen it enough times in a row so its real
            junction_hits = 0
            print("Junction seen - sensors were", LO, M, RO)   # DEBUG: shows WHY it thought this was a junction
            keep_going = handle_junction()
            last_junction_time = time.ticks_ms()
            lost_since = None
            return keep_going
        #not confirmed yet - KEEP STEERING while we check
        #if it's just a wobble, steering fixes it and the pattern goes away before it's confirmed
        steer(LO, M, RO)
        return True
    junction_hits = 0  #pattern broken, start counting again

    #normal line following
    if steer(LO, M, RO):
        lost_since = None     # we can see the line

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

        #BACKUP FOR CORNERS: the next instruction is a turn, but the line just vanished
        #-> we probably drove past a corner without noticing, so do the turn now
        #(at a corner the line ENDS, so losing it is a good sign that's where we are)
        #only if: the NEXT junction is a corner, AND we're not still settling after the last turn
        action = next_action()
        next_is_corner = (step + 1) in CORNERS
        cooled_down = time.ticks_diff(now, last_junction_time) > JUNCTION_COOLDOWN_MS
        if next_is_corner and cooled_down and (action == "left" or action == "right") and gone_for > MISSED_CORNER_MS:
            step += 1
            print("Junction", step, "->", action, "(missed the corner, turning now)")
            movement.stop()
            keep_going = spin_to_line(action, SPIN_MIN_MS)   # no driving forward - we're already past it
            last_junction_time = time.ticks_ms()
            lost_since = None
            return keep_going

        #otherwise its probably lost
        if gone_for > LOST_LIMIT_MS:
            movement.stop()
            print("Lost the line - stopping for safety")
            return False
 
    return True
