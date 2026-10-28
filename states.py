#the robot's states - main.py calls the current one about 100 times a second
#each function does a tiny bit each call and returns True only when its whole job is done
#
#  collecting -> checking_spaces -> delivering -> return_start
#
#navigation works in the background (main.py calls navigation.update()):
#  navigation.go_to(node) STARTS a journey and returns straight away
#  we know we've arrived when navigation.stage == "idle" and navigation.current_node == node

import navigation
import mapping
import movement
import debug
import grabber
import led
import time
import linefollowing

#tuning numbers
GRAB_TURN_MS = 150        # before grabbing, turn LEFT this long so the grabber covers more of the bay (0 = don't turn)
GRAB_TURN_SPEED = 60      # how fast to do that small turn
AFTER_GRAB_MS = 400       # AFTER grabbing, drive this much further in, so the 180 turn can find the line again
BACK_OFF_MS = 400         # after releasing, reverse this long so we don't hit the package when we turn
SLOT_MAX_MS = 3350        # driving into a rack slot: stop after this long even if the line hasn't ended
                          # (the grabber reaches the rack before the sensors reach the end of the line)

#memory
step = None               # where we are inside the current state: None = not started, "moving" = on the way
bay = None                # the collection bay we're going to
rack = None               # "A" or "B"
level = "bottom"          # "top" or "bottom" - TODO: read the magnet. bottom for now (no sensor yet)
target_slot = None        # the rack slot we chose
occupied_slots = []           # slots we've already filled TODO FOR DISTANCE
approach_start = None     # when we started driving into the rack slot
black_since = None        # when the sensors first saw all black on the way in (None = can see the line)

#measurements expected if full and empty
#occupied_threshold_mm= 150 TODO
#empty_threshold_mm= 20 TODO

#create list of collection bays to track which ones are visited
collection_bays= [17, 16, 38, 39]
checked_bays = [] #list of collection bays already checekd

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
    global step, bay, rack #,level TODO MAGNET SENSOR
    
    #incase or error ie.no rerading TODO Magnet
    if step == "magnet_error":
        return False

    #1. first call: choose a bay and start driving there
    if step is None:
        bay = None
        
        #check if node has been collected from already 
        for node in collection_bays:
            if node not in checked_bays:
                bay = node
                checked_bays.append(bay)
                print(bay)
                break
        
        #go to bay
        navigation.go_to(bay)
        step = "moving"
        return False

    #2. still on the way
    if not arrived(bay):
        return False

    #3. arrived (at the T's bar) - turn a little left, grab, then turn back straight
    movement.bay_mode = False     # back to normal speed (AFTER_GRAB_MS was tuned at normal speed)
    movement.spin_left(GRAB_TURN_SPEED)
    led.wait_ms(GRAB_TURN_MS)
    movement.stop()

    grabber.grab()
    
     #read magnet once box is collected TODO MAGNET SENSOR
    #pole= magnetsensor.read_magnet()

    #if pole== "north":
        #level = "top"
        #redorgreen.show_north()

    #elif pole== "south":
        #level = "bottom"
        #redorgreen.show_south()

    #for if no pole deteteced
    #else:
       # movement.stop()
       # redorgreen.pole_leds_off()
       # step= "magnet_error"
       # return False

    movement.spin_right(GRAB_TURN_SPEED)     # turn back the same amount, so we're straight again
    led.wait_ms(GRAB_TURN_MS)
    movement.stop()

    #now drive a bit further into the bay, so the u-turn after this ends up back on the line
    movement.move_forward()
    led.wait_ms(AFTER_GRAB_MS)
    movement.stop()

    #which rack: B if it came from a B bay, otherwise A
    if bay in mapping.collection_nodes["B"]:
        rack = "B"
    else:
        rack = "A"

    step = None                   # ready for the next state
    return True


def checking_spaces():
    #choose the NEAREST slot in the right rack that we haven't filled yet
    #TODO: actually check if each slot is occupied (distance sensor)
    global target_slot
    slots = mapping.storage_nodes[rack + "_" + level]      # e.g. "B" + "_" + "bottom" = "B_bottom"

    target_slot = None
    for slot in slots:
        if slot in occupied_slots:
            continue              # already filled, skip it
        if target_slot is None or distance(slot) < distance(target_slot):
            target_slot = slot    # nearest so far

    return target_slot is not None


def drive_into_slot():
    #one step of driving into the rack slot, following the line with steering
    #returns True when we should stop: the line has ended, OR we've been driving for SLOT_MAX_MS
    global black_since
    OL, IL, IR, OR = linefollowing.read_sensors()
    now = time.ticks_ms()

    #end of the line = all black for LINE_END_MS (300 ms) - the same rule as normal line following
    if OL == 0 and IL == 0 and IR == 0 and OR == 0:
        if black_since is None:
            black_since = now
        if time.ticks_diff(now, black_since) > linefollowing.LINE_END_MS:
            movement.stop()
            debug.log("SLOT: stopped because the LINE ENDED after", time.ticks_diff(now, approach_start), "ms")   # DEBUG
            return True
    else:
        black_since = None

    #backup: the grabber reaches the rack before the sensors reach the end of the line,
    #so stop after SLOT_MAX_MS even if the line hasn't ended (otherwise it would push against the rack forever)
    if time.ticks_diff(now, approach_start) > SLOT_MAX_MS:
        movement.stop()
        debug.log("SLOT: stopped because of the TIME LIMIT (SLOT_MAX_MS)")   # DEBUG
        return True

    #otherwise keep the line between the middle sensors
    if IL == 1 and IR == 0:
        movement.slight_left()      # line is to the left
    elif IR == 1 and IL == 0:
        movement.slight_right()     # line is to the right
    else:
        movement.move_forward()
    return False




#VS DELIVERY FUNCTION TO SORT
def delivering():
    global step

    #every delivery node is attached to a specific node that is on the main line, eg. delivery slot 15 is connected to 4 on the main line
    #we are coding our fuction to at that node turn in, turn distance sensor on and check if occupied
    #this prevents us from having to turn into every one

    # find the junction connected to the chosen slot
    #this takes the first value in the mapping dictionary attached to the target slot
    #each delivery node only conencted to one other node, so this node will be our junction that we want
    junction = next(iter(mapping.mapping[target_slot].values()))

    # find the compass direction from the junction into the slot
    slot_direction = mapping.direction_between(junction, target_slot)

    # 1. start travelling to the junction beside the slot
    if step is None:

    # rry to start the journey and store the result, sets journey_started to true if it has started
        journey_started = navigation.go_to(junction)

    # check whether it failed to start
        if journey_started == False:
            print("could not start journey to junction")
            return "error"

    #change the step so it knows its now travellign to junction
        step = "moving_to_junction"
        return False

    # 2. wait until we reach the junction
    if step == "moving_to_junction":
        if not arrived(junction):
            return False

        # work out the turn needed to face the slot
        #we do this by deciding what direction and hence action we need to take to move to the next junction ie. the delivery slot
        action = mapping.get_turn(navigation.heading, slot_direction)

        #if we are looking at the delivery bay, then action will be straight
        if action == "straight":
            # already facing the slot
            movement.stop()
            step = "checking"

        else:
            # start turning towards the slot
            linefollowing.start_turn(action)
            step = "turning"

        return False

    # 3. continue turning until the robot faces the slot
    if step == "turning":
        result = linefollowing.update_turn()

        #if turning fucnrion fails, call an error
        if result == "failed":
            movement.stop()
            print("could not turn towards slot")
            return "error"

        #if successfully turned into slot, stop movement
        if result is True:
            # Stop before entering the slot
            movement.stop()

            # remember which direction the robot is facing
            navigation.heading = slot_direction
            #set the next step to checking, so we know we are chekcing distance
            step = "checking"

        return False

    # 4. check the slot before entering
    if step == "checking":
        movement.stop()

        #take a reading using sensors
        reading = distancesensor.read_distance()
    
        # check for a missing or non-positive reading
        if reading is None or reading <= 0:
            print("invalid distance reading")
            return "error"

        if reading < occupied_threshold_mm:
            # the slot appears occupied is less than threshold
            # remember not to choose this slot again
            occupied_slots.append(target_slot)

            # ready to choose and travel to another slot
            step = None
            return "occupied"

        elif reading > empty_threshold_mm:
    # slot is empty, so start moving into it
            navigation.go_to(target_slot)
            step = "moving_to_slot"
            return False

        else:
            return "error"

    # 5. wait until we arrive at the slot
    if step == "moving_to_slot":
        if not arrived(target_slot):
            return False

        # 6. put the package down
        movement.stop()
        grabber.release()

        # back away from the package, to allow for 180 trun
        movement.move_backward()
        led.wait_ms(BACK_OFF_MS)
        movement.stop()

        # remember that we filled this slot
        used_slots.append(target_slot)

        step = None
        return "delivered"

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




#THONNY DELIVERY FUNCTION TO SORT
def delivering():
    global step, approach_start, black_since

    # start the journey to the delivery slot
    if step is None:
        navigation.go_to(target_slot)
        step = "moving"
        return False

    # once we have turned into the slot ie. next node is target slot and stage is clearing or travelling
    # take over from navigation, so we can stop on a time limit as well as at the end of the line
    if navigation.next_node == target_slot and navigation.stage in ("clearing", "travelling"):
        navigation.stage = "approaching"      # navigation ignores this stage, so it won't fight us for the motors
        movement.bay_mode = True              # drive in SLOWLY (same slow mode as the collection bays)
        approach_start = time.ticks_ms()
        debug.log("SLOT: driving into slot", target_slot)   # DEBUG
        black_since = None

    # driving into the slot, steering the whole way
    if navigation.stage == "approaching":
        if not drive_into_slot():
            return False                      # still driving in

        movement.bay_mode = False             # back to normal speed
        # tell navigation we have reached the delivery position manually
        navigation.current_node = target_slot
        navigation.heading = navigation.wanted
        navigation.stage = "idle"

    # still travelling towards the slot
    if not arrived(target_slot):
        return False

    # release the package and back away
    movement.stop()
    grabber.release()

    movement.move_backward()
    led.wait_ms(BACK_OFF_MS)
    movement.stop()

    used_slots.append(target_slot)
    grabber.reset_grabber()

    step = None
    return True
