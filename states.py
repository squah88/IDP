#the robot's states
#each function does a tiny bit each call and returns True only when its whole job is done
#collecting -> checking_spaces -> delivering -> return_start
#navigation works in the background (main.py calls navigation.update()):
#navigation.go_to(node) STARTS a journey and returns straight away
#we know we've arrived when navigation.stage == "idle" and navigation.current_node == node

import navigation
import mapping
import movement
import grabber
import led
import time
import linefollowing
import magnetsensor
import distancesensor

#tuning numbers
box_approach_ms = 200     #at a bay: drive forward this long before grabbing, so the grabber reaches the box
grab_turn_ms = 150        #before grabbing turn left this long so the grabber covers more of the bay
grab_turn_speed = 60      #how fast to do that small turn
after_grab_ms = 400       #after grabbing drive this much further in so the 180 turn can find the line again
back_off_ms = 400         #after releasing, reverse this long so we don't hit the package when we turn
slot_max_ms = 3350        #driving into a rack slot: stop after this long even if the line hasn't ended
check_drive_ms = 1000     #driving into a slot: drive this long, then stop and check if the slot is full - TODO: tune
occupied_mm = 150         #at the check point: closer than this = a package is already there - TODO: measure with testdistance.py
settle_before_check_ms = 300   #after stopping at the check point, wait this long before measuring

#memory
step = None               #where we are inside the current state: None = not started, "moving" = on the way
bay = None                #the collection bay we're going to
rack = None               #A or B
level = "bottom"          #top or bottom - TODO: read the magnet. bottom for now until we sort sensor out
target_slot = None        #the rack slot we chose
occupied_slots = []       #slots that are full
approach_start = None     #when we started driving into the rack slot
black_since = None        #when the sensors first saw all black on the way in (None = can see the line)
check_start = 0           #when we stopped at the check point (we wait a moment before measuring)

#the collection bays, in the order we visit them - we keep going round them because they get refilled
collection_bays = [17, 16, 38, 39]
next_bay = 0              #position in collection_bays of the bay to go to next (0 = bay 17)
 
def arrived(node):
    #True once navigation has finished and we're at this node
    return navigation.stage == "idle" and navigation.current_node == node
 
def distance(node):
    #how many nodes away this node is from where we are now (used to pick the nearest one)
    path = mapping.find_path(mapping.mapping, navigation.current_node, node)
    if path is None:
        return 999                # no route - treat as very far away
    return len(path)
 
def collecting():
    #returns False while still working, True once a package is collected,
    #or "empty" if the bay had no package (so main.py moves on to the next bay)
    global step, bay, rack, level, next_bay

    #step 1: choose the next bay (going round 17 -> 16 -> 38 -> 39 -> 17 ...) and start driving there
    if step is None:
        bay = collection_bays[next_bay]
        next_bay = (next_bay + 1) % len(collection_bays)    #% wraps back to 0 after the last bay

        navigation.go_to(bay)
        step = "moving"
        return False

    #step 2: still on the way
    if not arrived(bay):
        return False

    #step 3: arrived (at the T's bar) - drive a bit further in, turn a little left and grab
    movement.bay_mode = False     #back to normal speed
    movement.move_forward()
    led.wait_ms(box_approach_ms)
    movement.stop()

    movement.spin_left(grab_turn_speed)
    led.wait_ms(grab_turn_ms)
    movement.stop()

    grabber.grab()

    #read magnet once box is collected
    pole = magnetsensor.read_magnet()

    if pole == "north":
        level = "top"
        led.show_north()

    elif pole == "south":
        level = "bottom"
        led.show_south()

    #no pole detected = no package in this bay (not refilled yet)
    else:
        led.pole_leds_off()
        #put the grabber back down and open (lower first, so if something IS held it isn't dropped from high up)
        grabber.lift.move_to(grabber.DOWN_ANGLE)
        grabber.arm.move_to(grabber.OPEN_ANGLE_COLLECT)

    #turn back the same amount, so we're straight again
    movement.spin_right(grab_turn_speed)
    led.wait_ms(grab_turn_ms)
    movement.stop()

    #now drive a bit further into the bay, so the u-turn after this ends up back on the line
    movement.move_forward()
    led.wait_ms(after_grab_ms)
    movement.stop()

    step = None                   #ready for the next state

    #empty bay - tell main.py to try the next bay
    if pole is None:
        return "empty"

    #which rack: B if it came from a B bay, otherwise A
    if bay in mapping.collection_nodes["B"]:
        rack = "B"
    else:
        rack = "A"

    return True

def checking_spaces():
    #choose the NEAREST slot in the right rack that we haven't filled yet
    global target_slot
    slots = mapping.storage_nodes[rack + "_" + level]      # e.g. "B" + "_" + "bottom" = "B_bottom"

    target_slot = None
    for slot in slots:
        if slot in occupied_slots:
            continue              #already filled, skip it
        if target_slot is None or distance(slot) < distance(target_slot):
            target_slot = slot    #nearest so far
 
    return target_slot is not None
 
def drive_into_slot(limit_ms):
    #one step of driving into the rack slot, following the line with steering
    #returns True when we should stop: the line has ended or we've been driving for limit_ms
    global black_since
    OL, IL, IR, OR = linefollowing.read_sensors()
    now = time.ticks_ms()

    #end of the line = all black for line_end_ms - the same rule as normal line following
    if OL == 0 and IL == 0 and IR == 0 and OR == 0:
        if black_since is None:
            black_since = now
        if time.ticks_diff(now, black_since) > linefollowing.line_end_ms:
            movement.stop()
            return True
    else:
        black_since = None

    #stop after limit_ms even if the line hasn't ended
    #(the grabber reaches the rack before the sensors reach the end of the line)
    if time.ticks_diff(now, approach_start) > limit_ms:
        movement.stop()
        return True

    #otherwise keep the line between the middle sensors
    if IL == 1 and IR == 0:
        movement.slight_left()      #line is to the left
    elif IR == 1 and IL == 0:
        movement.slight_right()     #line is to the right
    else:
        movement.move_forward()
    return False

def arrive_at_slot():
    #tell navigation we are now at the slot, facing into it, and stopped
    #(navigation can't see this itself because we took over the driving)
    movement.bay_mode = False             #back to normal speed
    navigation.current_node = target_slot
    navigation.heading = navigation.wanted
    navigation.stage = "idle"

def delivering():
    #steps: drive to the slot -> drive partway in -> stop and measure distance
    #slot empty: drive the rest of the way in, drop the package, back off -> returns "delivered"
    #slot full: back off, then try another slot (navigation u-turns out next time) -> returns "occupied"
    #returns False while still working, "error" if something went wrong
    #we check from INSIDE the slot because the distance sensor sees in a cone,
    #so from the junction it would see the boxes in the slots either side too
    global step, approach_start, black_since, check_start

    #step 1: start the journey to the slot
    if step is None:
        if not navigation.go_to(target_slot):
            return "error"
        step = "moving_to_slot"
        return False

    #step 2: wait until we've turned onto the line into the slot, then take over from navigation
    if step == "moving_to_slot":
        if navigation.next_node == target_slot and navigation.stage in ("clearing", "travelling"):
            navigation.stage = "approaching"      #navigation ignores this stage, so it won't fight us for the motors
            movement.bay_mode = True              #drive in slowly
            approach_start = time.ticks_ms()
            black_since = None
            step = "driving_to_check"
        return False

    #step 3: drive partway into the slot, to where the sensor only sees this slot
    if step == "driving_to_check":
        if not drive_into_slot(check_drive_ms):
            return False                          #still driving
        check_start = time.ticks_ms()
        step = "checking"
        return False

    #step 4: stop and measure the distance to whatever is in front
    if step == "checking":
        movement.stop()

        #wait a moment so the robot has stopped wobbling before we measure
        if time.ticks_diff(time.ticks_ms(), check_start) < settle_before_check_ms:
            return False

        reading = distancesensor.read_distance()

        if reading is None:
            return "error"

        if reading < occupied_mm:
            #something close in front of us = a package is already in this slot
            occupied_slots.append(target_slot)

            #back away so there is room to turn round
            movement.move_backward()
            led.wait_ms(back_off_ms)
            movement.stop()

            #we are on the slot's line, facing into it - next journey starts with a u-turn
            arrive_at_slot()
            step = None
            return "occupied"

        #slot is empty - carry on driving in
        approach_start = time.ticks_ms()
        black_since = None
        step = "driving_in"
        return False

    #step 5: drive the rest of the way in
    if step == "driving_in":
        if not drive_into_slot(slot_max_ms - check_drive_ms):
            return False                          #still driving
        arrive_at_slot()

        #step 6: put the package down and back away
        movement.stop()
        grabber.release()

        movement.move_backward()
        led.wait_ms(back_off_ms)
        movement.stop()

        grabber.reset_grabber()
        led.pole_leds_off()                       #package delivered - pole lights off

        occupied_slots.append(target_slot)        #we just filled this slot
        step = None
        return "delivered"

    return False

def return_start():
    global step
 
    if step is None:
        navigation.go_to(mapping.home_node)
        step = "moving"
        return False
 
    if not arrived(mapping.home_node):
        return False
 
    movement.stop()
    step = None
    return True