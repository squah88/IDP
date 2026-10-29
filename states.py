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
grab_turn_ms = 150        #before grabbing turn left this long so the grabber covers more of the bay
grab_turn_speed = 60      #how fast to do that small turn
after_grab_ms = 400       #after grabbing drive this much further in so the 180 turn can find the line again
back_off_ms = 400         #after releasing, reverse this long so we don't hit the package when we turn
slot_max_ms = 3350        #driving into a rack slot: stop after this long even if the line hasn't ended
occupied_mm = 150         #facing a slot: closer than this = a package is already there - TODO: measure with test_distance.py
settle_before_check_ms = 300   #after turning to face a slot, wait this long before measuring

#memory
step = None               #where we are inside the current state: None = not started, "moving" = on the way
bay = None                #the collection bay we're going to
rack = None               #A or B
level = "bottom"          #top or bottom - TODO: read the magnet. bottom for now until we sort sensor out
target_slot = None        #the rack slot we chose
occupied_slots = []       #slots that are full
approach_start = None     #when we started driving into the rack slot
black_since = None        #when the sensors first saw all black on the way in (None = can see the line)
in_turn = None            #the turn we made at the junction to face the slot ("left"/"right"/"straight")
main_heading = None       #which way we were facing on the main line before turning to the slot
check_start = 0           #when we stopped in front of the slot (we wait a moment before measuring)

#create list of collection bays to track which ones are visited
collection_bays= [17, 16, 38, 39]
checked_bays = [] #list of collection bays already checked
 
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
    global step, bay, rack, level
    
    #error if the magnet sensor can't detect a pole
    if step == "magnet_error":
        return False
 
    #step 1: choose a bay and start driving there
    if step is None:
        bay = None
        
        #check if node has been collected from already 
        for node in collection_bays:
            if node not in checked_bays:
                bay = node
                #add to list as been checked 
                checked_bays.append(bay)
                break
        
        #go to bay
        navigation.go_to(bay)
        step = "moving"
        return False
 
    #step 2: still on the way
    if not arrived(bay):
        return False
 
    #step 3: arrived (at the T's bar) - turn a little left, grab, then turn back straight
    movement.bay_mode = False     #back to normal speed
    movement.spin_left(grab_turn_speed)
    led.wait_ms(grab_turn_ms)
    movement.stop()
 
    grabber.grab()
    
     #read magnet once box is collected 
    pole= magnetsensor.read_magnet()
 
    if pole == "north":
        level = "top"
        led.show_north()
 
    elif pole == "south":
        level = "bottom"
        led.show_south()
 
    #for if no pole detected
    else:
        movement.stop()
        led.pole_leds_off()
        step= "magnet_error"
        return False
 
    movement.spin_right(grab_turn_speed)     #turn back the same amount, so we're straight again
    led.wait_ms(grab_turn_ms)
    movement.stop()
 
    #now drive a bit further into the bay, so the u-turn after this ends up back on the line
    movement.move_forward()
    led.wait_ms(after_grab_ms)
    movement.stop()
 
    #which rack: B if it came from a B bay, otherwise A
    if bay in mapping.collection_nodes["B"]:
        rack = "B"
    else:
        rack = "A"
 
    step = None                   #ready for the next state
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
 
def drive_into_slot():
    #one step of driving into the rack slot, following the line with steering
    #returns True when we should stop: the line has ended or we've been driving for slot_max_ms
    global black_since
    OL, IL, IR, OR = linefollowing.read_sensors()
    now = time.ticks_ms()
 
    #end of the line = all black for LINE_END_MS - the same rule as normal line following
    if OL == 0 and IL == 0 and IR == 0 and OR == 0:
        if black_since is None:
            black_since = now
        if time.ticks_diff(now, black_since) > linefollowing.LINE_END_MS:
            movement.stop()
            return True
    else:
        black_since = None
 
    #backup: the grabber reaches the rack before the sensors reach the end of the line,
    #so stop after slot_max_ms even if the line hasn't ended
    if time.ticks_diff(now, approach_start) > slot_max_ms:
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
 
def slot_junction(slot):
    #the junction on the main line that a rack slot is attached to (e.g. slot 15 -> junction 4)
    #each slot is only connected to ONE node, so we just take the first (only) value
    for node in mapping.mapping[slot].values():
        return node
 
def opposite(turn):
    #the turn that undoes this turn
    if turn == "left":
        return "right"
    if turn == "right":
        return "left"
    return turn
 
def delivering():
    #steps: go to the junction next to the slot -> turn to face the slot -> measure distance
    #slot empty: drive in, drop the package, back off -> returns "delivered"
    #slot full: turn back to the main line, try another slot -> returns "occupied"
    #returns False while still working, "error" if something went wrong
    global step, approach_start, black_since, in_turn, main_heading, check_start
 
    junction = slot_junction(target_slot)
    slot_direction = mapping.direction_between(junction, target_slot)
 
    #step 1: start travelling to the junction beside the slot
    if step is None:
        if not navigation.go_to(junction):
            return "error"
        step = "moving_to_junction"
        return False
 
    #step 2: wait until we reach the junction then turn to face the slot
    if step == "moving_to_junction":
        if not arrived(junction):
            return False
 
        main_heading = navigation.heading                       #remember which way the main line goes
        in_turn = mapping.get_turn(navigation.heading, slot_direction)

        if in_turn == "straight":
            movement.stop()
            check_start = time.ticks_ms()
            step = "checking"
        else:
            linefollowing.start_turn(in_turn)
            step = "turning_in"
        return False
 
    #step 3: keep turning until we face the slot
    if step == "turning_in":
        result = linefollowing.update_turn()
        if result == "failed":
            movement.stop()
            return "error"
        if result is True:
            movement.stop()
            navigation.heading = slot_direction
            check_start = time.ticks_ms()
            step = "checking"
        return False
 
    #step 4: check the slot with the distance sensor
    if step == "checking":
        movement.stop()
 
        #wait a moment so the robot has stopped wobbling before we measure
        if time.ticks_diff(time.ticks_ms(), check_start) < settle_before_check_ms:
            return False
 
        reading = distancesensor.read_distance()
 
        if reading is None:
            return "error"
 
        if reading < occupied_mm:
            #something close in front of us = a package is already there
            occupied_slots.append(target_slot)
 
            if in_turn == "straight":
                step = None
                return "occupied"
 
            #turn back onto the main line, spinning on the spot (our wheels are already over the junction)
            linefollowing.start_turn(opposite(in_turn), forward_first=False)
            step = "turning_back"
            return False
 
        #slot is empty - drive in
        navigation.go_to(target_slot)
        step = "moving_to_slot"
        return False
 
    #step 5: slot was full - turn back to face along the main line, then go and try another slot
    if step == "turning_back":
        result = linefollowing.update_turn()
        if result == "failed":
            movement.stop()
            return "error"
        if result is True:
            movement.stop()
            navigation.heading = main_heading
            step = None
            return "occupied"
        return False
 
    #step 6: driving into the slot
    if step == "moving_to_slot":
        #once we're on the line into the slot, take over from navigation
        #so we can stop on a time limit as well as at the end of the line
        if navigation.next_node == target_slot and navigation.stage in ("clearing", "travelling"):
            navigation.stage = "approaching"      #navigation ignores this stage, so it won't fight us for the motors
            movement.bay_mode = True              #drive in slowly
            approach_start = time.ticks_ms()
            black_since = None
 
        if navigation.stage == "approaching":
            if not drive_into_slot():
                return False                      #still driving in
 
            movement.bay_mode = False             #back to normal speed
            # tell navigation we have reached the slot
            navigation.current_node = target_slot
            navigation.heading = navigation.wanted
            navigation.stage = "idle"
 
        if not arrived(target_slot):
            return False
 
        #step 7:put the package down and back away
        movement.stop()
        grabber.release()
 
        movement.move_backward()
        led.wait_ms(back_off_ms)
        movement.stop()
 
        grabber.reset_grabber()
        led.pole_leds_off()                #package delivered - pole lights off
 
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