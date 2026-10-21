#creating map for each junction

#import queue functions, so route can be added as a queue
from collections import deque

#use BFS route planner to find the shortest route to node
#use nodes, where attaching available directions are clarified
#we have mapped so north is facing traffic lights at start

# robot's actual position and starting orientation.
current_node = 0
heading = "N"

#make map for nodes- see google drive for drawing of map
map = {
    # start and start-box boundaries
    0:  {"N": 18, "E": 1, "W": 37},
    1:  {"W": 0, "E": 55},
    18: {"S": 0, "N": 19},
    37: {"E": 0, "W": 54},

    # bottom corners
    54: {"E": 37, "N": 52},
    55: {"W": 1, "N": 2},

    # right-hand main line ie. B
    2: {"S": 55, "N": 3, "W": 17},
    3: {"S": 2, "N": 4, "W": 16},
    4: {"S": 3, "N": 5, "W": 15},
    5: {"S": 4, "N": 6, "W": 14},
    6: {"S": 5, "N": 7, "W": 13},
    7: {"S": 6, "N": 8, "W": 12},
    8: {"S": 7, "N": 9, "W": 11},
    9: {"S": 8, "W": 10},

    # right-hand rack endpoints, drop off points ie. bottom rack B
    10: {"E": 9},
    11: {"E": 8},
    12: {"E": 7},
    13: {"E": 6},
    14: {"E": 5},
    15: {"E": 4},

    # right-hand collection endpoints, pick up boxes ie. B
    16: {"E": 3},
    17: {"E": 2},

    # centre main line ie. top part
    19: {"S": 18, "N": 20, "W": 30, "E": 36},
    20: {"S": 19, "N": 21, "W": 29, "E": 35},
    21: {"S": 20, "N": 22, "W": 28, "E": 34},
    22: {"S": 21, "N": 23, "W": 27, "E": 33},
    23: {"S": 22, "N": 24, "W": 26, "E": 32},
    24: {"S": 23, "W": 25, "E": 31},

    # centre rack endpoints on the left side ie. top rack A
    25: {"E": 24},
    26: {"E": 23},
    27: {"E": 22},
    28: {"E": 21},
    29: {"E": 20},
    30: {"E": 19},

    # Centre rack endpoints on the right side ie. top rack B
    31: {"W": 24},
    32: {"W": 23},
    33: {"W": 22},
    34: {"W": 21},
    35: {"W": 20},
    36: {"W": 19},

    # left-hand collection junctions, pick up boxes ie. A
    52: {"S": 54, "N": 53, "E": 38},
    53: {"S": 52, "N": 40, "E": 39},

    # left-hand collection endpoints ie. A
    38: {"W": 52},
    39: {"W": 53},

    # left-hand main line ie. A
    40: {"S": 53, "N": 41, "E": 51},
    41: {"S": 40, "N": 42, "E": 50},
    42: {"S": 41, "N": 43, "E": 49},
    43: {"S": 42, "N": 44, "E": 48},
    44: {"S": 43, "N": 45, "E": 47},
    45: {"S": 44, "E": 46},

    # left-hand rack endpoints, drop off ie. bottom rack A
    46: {"W": 45},
    47: {"W": 44},
    48: {"W": 43},
    49: {"W": 42},
    50: {"W": 41},
    51: {"W": 40}
}


#create bfs code
#start by creating a function that finds the correct path
#it does this by taking starting node, target and the dictionary of nodes
#from the starting nodes it considers the nodes attached to this
#it then considers the nodes attached to those nodes and continues to do so
#stops once it hits the target node


def find_path(map, curr_node, target):
    # graph is your map dictionary
    # curr_node is the starting node
    # target is the node we want to reach

    # if we are already at the target, no travelling is needed, so return current node
    if curr_node == target:
        return [curr_node]

    # remember how we discovered each node
    # eg. parents[1] = 0 means we found node 1 from node 0 ie. 0 : 1
    # starting node has no parent
    parents = {curr_node: None}

    # create waiting list of nodes whose connections need checking
    # initially, only the starting node is waiting
    # ie. if queue is 0 1 2
    # 0 conencts to 1 and 2
    # 1 connects to 3 4
    # 2 connected to 5 6
    # thus queue is as follows
    # after 0 -> 1 2
    # after 1 -> 3 4 5
    #after 2 -> 3 4 5 6
    # these will be added to queue
    #note that 2 appears twice, so we must ensure 2 it is not counted again when considering node 3, despite being attached to 3
    queue = deque([curr_node])

    # keep searching while there are nodes waiting in the queue.
    while queue:

        # remove the first waiting node and place it in node to check it next
        node = queue.popleft()

        # look at every node connected to this node
        # .values() gives the node numbers, without the directions
        # for neightbour, means that for every node value attached to current node, is being considered
        for neighbour in map[node].values():

            # skip missing connections or nodes already discovered
            #prevents the search repeatedly going around loops
            if neighbour is None or neighbour in parents:
                #continue means it skips it and just moves onto next attaching node
                continue

            # remember which node led us to this neighbour
            #place this back into the parents list to keep track of route
            parents[neighbour] = node
            #essentialy parents[1] = 0, means that 0 will be added to node 1 route

            # if this neighbour is our target, rebuild the route
            if neighbour == target:

                # start the route list with the target
                # ie. the neighbour ie. the current node we have discovered ie. the target
                path = [neighbour]

                # path[-1] means the last node in the path list
                # keep adding its parent until we reach the start
                # it back tracks the route essentially
                # starting with target, we check its parent in the dictionary
                # we then set that parent as the new current mode and find its parent and so on
                #we add this to our path list
                while parents[path[-1]] is not None:
                    path.append(parents[path[-1]])

                # list currently runs from target back to start
                # reverse it so it runs from start to target
                return path[::-1]

            # if this is not the target, add it to the queue
            # so we can check its connections later
            # ensures we reset back to checking next value in list
            queue.append(neighbour)

    # if the queue becomes empty without finding the target,
    # there is no route to it.
    return None

#we now need to translate our path into the directions and instructions to follow
#start by defining function that finds direction between two nodes
def direction_between(current, next_node):
    # look through the connections at the current node
    #first variable is the direction, and its attachement in the dictionary is the node
    #if we test each direction and see if its attachment is our target then that is our direction
    for direction, neighbour in map[current].items():

        # return the compass direction leading to the next node
        if neighbour == next_node:
            return direction

    return None

#now make instructions
#heading is direction robot is currently in
def make_instructions(path, heading):
    # Compass directions arranged clockwise.
    compass = ["N", "E", "S", "W"]

    # Corresponding actions for 0, 1, 2 or 3 clockwise quarter-turns.
    actions = ["straight", "right", "u_turn", "left"]

    # Store the instructions here.
    instructions = []

    # Look at each consecutive pair of nodes in the path.
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]

        # Find which compass direction leads to the next node.
        wanted = direction_between(current, next_node)

        if wanted is None:
            raise ValueError("Path contains unconnected nodes")

        # Compare the wanted direction with the robot's heading.
        difference = (
            compass.index(wanted) - compass.index(heading)
        ) % 4

        # Save the action and the node it leads to.
        instructions.append((actions[difference], next_node))

        # For planning the next instruction, assume this turn succeeds.
        heading = wanted

    return instructions





