########## MAIN ##########

import time
import movement
import linefollowing
import led
from machine import Pin


#set a power pin for sensors and led
power = Pin(28, Pin.OUT)

#BUTTON CODE
#set button pin to be an input, the pin pull up mean the button is high normally, and when pressed it will be 
button = Pin(15, Pin.IN, Pin.PULL_UP)

#running variable to keep track of if robot is on or off, start with off
running = False

#previous state variable to keep track of the button state, start with high because button is not pressed
previous_state = 1

#the button value is 1 when not pressed, and 0 when pressed
#set loop that runs always using while True:

######NORMAL CODE
#while True:
    #set that current_state is equal to the button value
#    current_state = button.value()
    
    # detect a new press: released (1) to pressed (0)
#    if previous_state == 1 and current_state == 0:
#        # change running to the opposite of what it was before
#        running = not running

        #set conditions for what happens if not running, versus running
#        if not running:
#            led.led_off()
#            movement.stop()
#        else:
#            led.flash_led(1, 0.1) 

    #update previous_state to be equal to current_state for the next loop
#    previous_state = current_state

    #set condition for if running
#    if running:
#        led.flash_led(1, 0.1)  # flash LED many times with a 0.1 second interval
#        linesensor.follow_line()


#######FOR THE LINE TEST
while True:
    #set that current_state is equal to the button value
    current_state = button.value()
    
    # detect a new press: released (1) to pressed (0)
    if previous_state == 1 and current_state == 0:
        # change running to the opposite of what it was before
        running = not running

        #set conditions for what happens if not running, versus running
        if running:
            linefollowing.reset_route()  #start from the first instruction
            print("Starting route")
        else:
            movement.stop()
            led.led_off()
            print("Stopped by button")

        time.sleep(0.2)  #debounce delay

    #update previous_state to be equal to current_state for the next loop
    previous_state = current_state

    #set condition for if running
    if running:
        led.update_flash()  #flash LED without blocking the rest of the code
        keep_going = linefollowing.follow_line()  #one step of the line following code, returns True if we should keep going, False if we have finished the route
        
        if not keep_going:
            running = False
            movement.stop()
            led.led_off()
        
    time.sleep(0.01) #short pause so the loop runs about 100 times per second, which is a good speed for the line following code to run at

########### LINE SENSOR CODE ##########
#line sensors + route following
#4 sensors in a row at the front:  [OL]   [IL][IR]   [OR]
#inner pair (IL, IR) = steering, outer pair (OL, OR) = spotting junctions
#each sensor reads 1 = white (or red), 0 = black

import led
from machine import Pin
import time
import movement

#sensor pins (GP numbers) - CHECK THESE MATCH YOUR WIRING
outer_left = Pin(11, Pin.IN)
inner_left = Pin(12, Pin.IN)
inner_right = Pin(13, Pin.IN)
outer_right = Pin(14, Pin.IN)   # NOTE: the LED in led.py must NOT also be on GP14

#what to do at each junction, in order
ROUTE = [
    "straight",        # 1.  crossroad: right-hand edge of start box
    "left",            # 2.  bottom-right corner
    "left",            # 3.  T-junction to the lower box
    "junction_u_turn", # 4.  T-junction touching the collection point
    "left",            # 5.  T-junction back on the right-hand line
    "straight",        # 6.  T-junction to the upper box
    "left",            # 7.  T-junction to the line on the left
    "end_u_turn",      # 8.  end of that line (not a junction - the line just stops)
    "right",           # 9.  T-junction back on the right-hand line
    "straight",        # 10. T-junction to the upper box
    "straight",        # 11. T-junction to the lower box
    "right",           # 12. bottom-right corner
    "straight",        # 13. crossroad: right-hand edge of start box
    "end",             # 14. start spot
]

#tuning numbers
JUNCTION_CONFIRM = 2          # junction must be seen this many readings in a row
JUNCTION_COOLDOWN_MS = 500    # after a junction, ignore junctions for this long
START_IGNORE_MS = 1500        # at the start, ignore junctions for this long (the start spot is a junction)
DRIVE_PAST_MS = 800           # before a turn, drive forward this long so the wheels are over the junction
STRAIGHT_MS = 300             # drive this long to get over a junction we go straight over
SPIN_MIN_MS = 150             # always spin at least this long before looking for the line
SPIN_MIN_180_MS = 1500        # u-turns: spin this long BLIND first, so it ends up past 90 degrees before looking for the line
LINE_END_MS = 300             # line gone this long = the end of the line
LOST_LIMIT_MS = 1500          # line gone this long = lost, stop
CORNERS = [2, 5, 9, 12]       # junctions where the line we're ON ends (corners, and T-junctions we hit head-on)
                              # 2, 12 = bottom-right corner, 5, 9 = coming back onto the right-hand line
MISSED_CORNER_MS = 150        # at a corner: line gone this long = we've reached the corner, turn now
BAR_SKIP_MS = 500             # at the box: drive this long first to get off the T's bar
BOX_EXTRA_MS = 400            # at the box: drive this much further onto the red
BOX_TIMEOUT_MS = 3000         # at the box: give up looking for red after this long
END_MS = 800                  # at the start spot: drive this long then stop

#memory between loops
step = 0                  # which instruction in ROUTE is next
junction_hits = 0         # how many readings in a row looked like a junction
last_junction_time = 0    # when we last handled a junction
lost_since = None         # when we lost the line (None = we can see it)


def log(*parts):
    #like print, but ALSO saves the message to log.txt on the Pico
    #so you can read what happened after a run without the laptop plugged in
    message = " ".join(str(p) for p in parts)
    print(message)
    with open("log.txt", "a") as f:     # "a" = add to the end of the file
        f.write(message + "\n")


def read_sensors():
    #returns left to right: outer left, inner left, inner right, outer right
    return outer_left.value(), inner_left.value(), inner_right.value(), outer_right.value()


def reset_route():
    #call when the robot starts
    global step, junction_hits, last_junction_time, lost_since
    step = 0
    junction_hits = 0
    #set the "last junction" time in the future so junctions are ignored for START_IGNORE_MS
    last_junction_time = time.ticks_add(time.ticks_ms(), START_IGNORE_MS - JUNCTION_COOLDOWN_MS)
    lost_since = None
    open("log.txt", "w").close()        # "w" = start a fresh, empty log for this run
    log("Starting route")


def next_action():
    #the next instruction, or None if the route is finished
    if step < len(ROUTE):
        return ROUTE[step]
    return None


def steer(OL, IL, IR, OR):
    #small corrections using the inner sensors. returns False if no sensor sees the line
    if IL and IR:
        movement.move_forward()     # line between the inner sensors
    elif IL or OL:
        movement.slight_left()      # line is to the left
    elif IR or OR:
        movement.slight_right()     # line is to the right
    else:
        return False
    return True


def spin_to_line(direction, min_ms):
    #spin until the new line is between the inner sensors
    #spinning left, the inner LEFT sensor reaches the line first, so wait for the inner RIGHT one (and vice versa)
    if direction == "left":
        movement.spin_left()
        second = inner_right
    else:
        movement.spin_right()
        second = inner_left
    led.wait_ms(min_ms)
    while inner_left.value() or inner_right.value():   # spin off the old line (or the red box)
        led.update_flash()
    while not second.value():                          # spin until the new line is centred
        led.update_flash()
    movement.stop()


def box_u_turn():
    #collection point: drive up to the red box, then turn round
    movement.move_forward()
    led.wait_ms(BAR_SKIP_MS)                           # get off the T's bar first (it's white too)
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < BOX_TIMEOUT_MS:   # give up after BOX_TIMEOUT_MS
        OL, IL, IR, OR = read_sensors()
        if IL and IR and (OL or OR):                   # both inner + at least one outer see red = we're at the box
            break
        steer(OL, IL, IR, OR)                          # otherwise keep following the line towards it
        led.wait_ms(10)
    movement.move_forward()
    led.wait_ms(BOX_EXTRA_MS)                          # a bit further onto the red
    log("At the red box - u-turn")
    spin_to_line("left", SPIN_MIN_180_MS)


def handle_junction():
    #do the next instruction. returns True to keep going, False to stop
    global step
    action = next_action()
    step += 1
    log("Junction", step, "->", action)

    if action == "straight":
        movement.move_forward()
        led.wait_ms(STRAIGHT_MS)
    elif action == "left" or action == "right":
        movement.move_forward()
        led.wait_ms(DRIVE_PAST_MS)
        spin_to_line(action, SPIN_MIN_MS)
    elif action == "junction_u_turn":
        box_u_turn()
    elif action == "end":
        movement.move_forward()
        led.wait_ms(END_MS)
        log("Back at the start - route complete!")
        return False
    return True


def is_junction(OL, OR):
    #an outer sensor sees a line, on the side the route needs
    action = next_action()
    if action == "left":
        return OL == 1
    if action == "right":
        return OR == 1
    if action == "end_u_turn" or action is None:
        return False                # not expecting a junction here
    return OL == 1 or OR == 1       # straight / u-turn / end: either side


def follow_line():
    #one step of line following. returns True to keep going, False to stop
    global step, junction_hits, last_junction_time, lost_since
    OL, IL, IR, OR = read_sensors()
    now = time.ticks_ms()

    #1. junctions
    if is_junction(OL, OR) and time.ticks_diff(now, last_junction_time) > JUNCTION_COOLDOWN_MS:
        junction_hits += 1
        if junction_hits >= JUNCTION_CONFIRM:
            junction_hits = 0
            log("Junction seen - sensors were", OL, IL, IR, OR)   # DEBUG
            keep_going = handle_junction()
            last_junction_time = time.ticks_ms()
            lost_since = None
            return keep_going
    else:
        junction_hits = 0

    #2. steering
    if steer(OL, IL, IR, OR):
        lost_since = None
        return True

    #3. can't see the line
    if lost_since is None:
        lost_since = now
    gone_for = time.ticks_diff(now, lost_since)

    if next_action() == "end_u_turn" and gone_for > LINE_END_MS:
        step += 1
        log("Step", step, "-> end of line, u-turn")
        spin_to_line("left", SPIN_MIN_180_MS)
        last_junction_time = time.ticks_ms()
        lost_since = None
    elif (step + 1) in CORNERS and gone_for > MISSED_CORNER_MS and time.ticks_diff(now, last_junction_time) > JUNCTION_COOLDOWN_MS:
        #backup for corners: the next junction is a corner and the line has ended, so turn now
        action = next_action()
        step += 1
        log("Junction", step, "->", action, "(line ended at corner)")
        spin_to_line(action, SPIN_MIN_MS)
        last_junction_time = time.ticks_ms()
        lost_since = None
    elif gone_for > LOST_LIMIT_MS:
        log("Lost the line - stopping")
        return False
    return True
