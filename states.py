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

#tuning numbers
BOX_APPROACH_MS = 400     # at a bay we stop at the T's bar - drive this much further into the bay before grabbing
BACK_OFF_MS = 400         # after releasing, reverse this long so we don't hit the package when we turn

#memory
step = None               # where we are inside the current state: None = not started, "moving" = on the way
bay = None                # the collection bay we're going to
rack = None               # "A" or "B"
level = "bottom"          # "top" or "bottom" - TODO: read the magnet. bottom for now (no sensor yet)
target_slot = None        # the rack slot we chose
used_slots = []           # slots we've already filled

#create list of collection bays to track which ones are visited
collection_bays= [17, 16, 38, 39]
checked_bays = set() #list of collection bays already checekd

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
    global step, bay, rack

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
        if slot in used_slots:
            continue              # already filled, skip it
        if target_slot is None or distance(slot) < distance(target_slot):
            target_slot = slot    # nearest so far

    return target_slot is not None


def delivering():
    global step

    #1. first call: start driving to the slot
    if step is None:
        navigation.go_to(target_slot)
        step = "moving"
        return False

    #2. still on the way
    if not arrived(target_slot):
        return False

    #3. arrived - put it down, then back away from it
    movement.stop()
    grabber.release()
    movement.move_backward()
    led.wait_ms(BACK_OFF_MS)
    movement.stop()
    used_slots.append(target_slot)

    step = None
    return True


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




