#takes the robot from node to node along a route

import mapping
import time
import linefollowing
import movement

#where the robot is and which way it faces (main.py sets these when the button is pressed)
current_node = 0
facing = "N"

target = None       #the node we are going to
next_node = None    #the next node on the route
wanted = None       #the compass direction we need to face to reach next_node
came_from = None    #the node we were at before this one (to know if we just left a slot or bay)

stage = "idle"

def go_to(destination):
    #start a journey to destination - returns False if we're already busy with one
    global target, came_from

    #only accept a new destination when stopped at a known node
    if stage != "idle":
        return False

    target = destination
    came_from = None
    plan_connection()    #plan the first step
    return True

def plan_connection():
    #plan and start the next step of the route (straight on, or a turn)
    global stage, next_node, wanted

    #already at the destination - finished
    if current_node == target:
        movement.stop()
        stage = "idle"
        return

    #ask mapping for the next move: which turn, which node, which direction
    move = mapping.plan_move(current_node, target, facing)

    #no route found
    if move is None:
        movement.stop()
        stage = "error"
        return

    action, next_node, wanted = move

    #straight on so just drive off the junction
    if action == "straight":
        movement.move_forward()
        stage = "clearing"

    #left, right or u-turn
    else:
        #if the agv just came out of a rack slot or bay onto the main line the next junction is very close so ask the turn to reverse a bit at the end
        left_dead_end = came_from in mapping.line_end_nodes or came_from in mapping.collection_nodes["A"] or came_from in mapping.collection_nodes["B"]
        linefollowing.start_turn(action, reverse_at_end=left_dead_end)
        stage = "turning"

def update():
    #update the robot's journey - called every loop from main.py
    global stage, current_node, facing, came_from

    #nothing to do
    if stage == "idle" or stage == "error":
        return

    #bay mode on while we're driving into a collection bay
    #states.py also switches it on while driving into a rack slot
    if stage == "turning":
        movement.bay_mode = False
    elif stage == "clearing" or stage == "travelling":
        movement.bay_mode = next_node in mapping.collection_nodes["A"] or next_node in mapping.collection_nodes["B"]

    #if we are turning
    if stage == "turning":
        result = linefollowing.update_turn()

        #turn gave up
        if result == "failed":
            movement.stop()
            stage = "error"

        #turn finished
        elif result:
            facing = wanted
            stage = "clearing"
        return

    #clearing - drive off the old junction before looking for the next one
    if stage == "clearing":
        OL, IL, IR, OR = linefollowing.read_sensors()

        #all black for too long = we've driven off the line
        if OL == 0 and IL == 0 and IR == 0 and OR == 0:

            #if we have just lost the line, start a timer
            if linefollowing.lost_since is None:
                linefollowing.lost_since = time.ticks_ms()

            #if we've been off the line for too long, stop and error
            elif time.ticks_diff(time.ticks_ms(), linefollowing.lost_since) > linefollowing.lost_limit_ms:
                movement.stop()
                linefollowing.lost_since = None
                stage = "error"
                return
        else:
            linefollowing.lost_since = None

        #move forward, straightening up with the middle two sensors (fixes a turn that finished crooked)
        if IL == 1 and IR == 0:
            movement.slight_left()      #line is to the left
        elif IR == 1 and IL == 0:
            movement.slight_right()     #line is to the right
        else:
            movement.move_forward()

        #outer sensors black + a middle sensor on the line = off the junction, back on ordinary line
        if OL == 0 and OR == 0 and (IL == 1 or IR == 1):
            stage = "travelling"
        return

    #travelling - normal line following until the next node
    if stage == "travelling":
        #tell line following the next node, so it knows whether to expect a line end
        result = linefollowing.following_line(next_node)

        #reached a node - assume it is the one we were going for
        if result == "node":
            came_from = current_node
            current_node = next_node
            facing = wanted

            #plan the next step or finish if this was the target
            plan_connection()

        #lost the line - stop
        elif result == "lost":
            movement.stop()
            stage = "error"
