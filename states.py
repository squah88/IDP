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
import grabber
import led
from machine import Pin
import redorgreen
import linefollowing
import distancesensor
import magnetsensor


#tuning numbers
BOX_APPROACH_MS = 400     # at a bay we stop at the T's bar - drive this much further into the bay before grabbing
BACK_OFF_MS = 400         # after releasing, reverse this long so we don't hit the package when we turn

#memory
step = None               # where we are inside the current state: None = not started, "moving" = on the way
bay = None                # the collection bay we're going to
rack = None               # "A" or "B"
level = "bottom"          # "top" or "bottom"
target_slot = None        # the rack slot we chose
used_slots = []           # slots we've already filled

#create list of collection bays to track which ones are visited
collection_bays= [17, 16, 38, 39]
checked_bays = set() #list of collection bays already checekd

# keep track of slots found occupied by the distance sensor
occupied_slots = []

#measurement expected if full and empty
occupied_threshold_mm= 150
empty_threshold_mm= 200

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

     #incase of error ie. no reading
    if step == "magnet_error":
        return False
            

    #1. first call: choose a bay and start driving there
    if step is None:
        bay = None
        
        #check if node has been collected from already 
        for node in collection_bays:
            if node not in checked_bays:
                bay = node
                break


   
        #go to bay
        navigation.go_to(bay)
        step = "moving"
        return False

    #2. still on the way
    if not arrived(bay):
        return False

    #3. arrived (at the T's bar) - drive onto the red and grab
    movement.move_forward()
    led.wait_ms(BOX_APPROACH_MS)
    movement.stop()
    grabber.grab()

    #read magnet once box is collected
    pole= magnetsensor.read_magnet()

    if pole== "north":
        level = "top"
        redorgreen.show_north()

    elif pole== "south":
        level = "bottom"
        redorgreen.show_south()

    #for if no pole deteteced
    else:
        movement.stop()
        redorgreen.pole_leds_off()
        step= "magnet_error"
        return False


    #which rack: B if it came from a B bay, otherwise A
    if bay in mapping.collection_nodes["B"]:
        rack = "B"
    else:
        rack = "A"

    step = None                   # ready for the next state
    return True


def checking_spaces():
    #choose the NEAREST slot in the right rack that we haven't filled yet
    global target_slot
    #this creates a list of all the slots in each thing ie bottom B
    slots = mapping.storage_nodes[rack + "_" + level]      # e.g. "B" + "_" + "bottom" = "B_bottom"

    #create a variable for the current slot we are targetting
    target_slot = None
    #check that our list of slots is not already used or occupied 
    for slot in slots:
        if slot in used_slots or slot in occupied_slots:
            continue              # already filled, skip it, if already checked and is occupied, skip it

        #choose nearesr remaining slot
        if target_slot is None or distance(slot) < distance(target_slot):
            target_slot = slot    # nearest so far

    return target_slot is not None


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




