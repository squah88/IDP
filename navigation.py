import mapping
import time
import linefollowing
import movement

#where the robot is and which way it faces (main.py sets these when the button is pressed)
current_node = 0
heading = "E"

#set what our target is and what the next node is to get to target is and the wanted direction we want to point
target = None
next_node = None
wanted = None

#set current stage we are at- idle, turning, travelling (following line to next node), clearing (moving off old junctino)
stage = "idle"

#create function that accepts a destination to go to 
#this function ensures we do not assign a new action before first action carried out
def go_to(destination):
    global target

    #only accept a new destination when stopped at a known node so if not idle at a node do not continues
    if stage != "idle":
        return False

    #set our target to destination point
    target = destination
    #plan first connection node
    plan_connection()
    return True


#plan next action
def plan_connection():
    global stage, next_node, wanted

    #start for if the destination is already at node, just go idle
    if current_node == target:
        movement.stop()
        stage = "idle"
        return

    #choose the next connection, set move to equal new action, new node, new direction
    move = mapping.plan_move(current_node, target, heading)

    #if there is no move, then no route found
    if move is None:
        movement.stop()
        stage = "error"
        return

    #assign what each varibale of move is 
    action, next_node, wanted = move

    #if action is straight go forward
    #change stage to clearing, so that when goto called it doesnt accept a new direction
    if action == "straight":
        movement.move_forward()
        stage = "clearing"

    #if action is not straight, then turn and change stage
    else:
        linefollowing.start_turn(action)
        stage = "turning"

#function to update the stage robot is in, so it knows when done action and can get next instuction
def update():
    global stage, current_node, heading

    #if stage is already idle or if it is an error, it jsut returns function ie. do nothing
    if stage == "idle" or stage == "error":
        return

    #bay mode on while we're driving into a collection bay
    #(states.py also switches it on while driving into a rack slot)
    if stage == "turning":
        movement.bay_mode = False
    elif stage == "clearing" or stage == "travelling":
        movement.bay_mode = next_node in mapping.collection_nodes["A"] or next_node in mapping.collection_nodes["B"]

#if we are turning
    if stage == "turning":
        #continue the requested turn until aligned
        result = linefollowing.update_turn()

        #turn gave up
        if result == "failed":
            movement.stop()
            stage = "error"

        elif result:
            #when true, we change the new direction our robot is in to what we wanted it to be and change stage
            heading = wanted
            stage = "clearing"
        return

#if we are clearing, it means we are moving off old junction
#we need to start moving forward beffore tracking, to prevent it from reading the same junction
    if stage == "clearing":
        #move off the current junction before detecting another
        #start by reading the sensors
        OL, IL, IR, OR = linefollowing.read_sensors()

        #all black for too long = we've driven off the line
        if OL == 0 and IL == 0 and IR == 0 and OR == 0:
            #if we have just lost the line, start a timer
            if linefollowing.lost_since is None:
                linefollowing.lost_since = time.ticks_ms()
            #if we've been off the line for too long, stop and error
            elif time.ticks_diff(time.ticks_ms(), linefollowing.lost_since) > linefollowing.LOST_LIMIT_MS:
                movement.stop()
                linefollowing.lost_since = None
                stage = "error"
                return
        else:
            linefollowing.lost_since = None

        #move forward, but straighten up using the middle two sensors (outer ones are ignored here)
        #this fixes a turn that finished slightly crooked
        if IL == 1 and IR == 0:
            movement.slight_left()      #line is to the left
        elif IR == 1 and IL == 0:
            movement.slight_right()     #line is to the right
        else:
            movement.move_forward()

        # only enable arrival detection once back on ordinary line
        if OL == 0 and OR == 0 and (IL == 1 or IR == 1):
            #change stage to travelling
            stage = "travelling"
        return

#travelling just means that it is following route, so normal line follwowing, continues this until it sees node
    if stage == "travelling":
        #give following line next node to see if it expects an endpoint
        result = linefollowing.following_line(next_node)
        #our line following sends back "node" if it tracks a node

        #if node is detected we need to execute next node to find
        if result == "node":
            #assume the next detected node is the expected one, ie. the node we travelled to
            #update this, direction and node
            current_node = next_node
            heading = wanted

            #choose the next connection, or finish
            plan_connection()


    #if robot is lost, stop movement and make stage error
        elif result == "lost":
            movement.stop()
            stage = "error"