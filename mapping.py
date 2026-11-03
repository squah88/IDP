#creating map for each junction

#use breadth first search route planner to find the shortest route to node
#we have mapped so north is facing traffic lights at start

#make map for nodes - see google drive for drawing of map
mapping = {
    #start and start-box boundaries
    0:  {"N": 18, "E": 1, "W": 37},
    1:  {"W": 0, "E": 55},
    18: {"S": 0, "N": 19},
    37: {"E": 0, "W": 54},

    #bottom corners
    54: {"E": 37, "N": 52},
    55: {"W": 1, "N": 2},

    #right-hand main line ie. B
    2: {"S": 55, "N": 3, "W": 17},
    3: {"S": 2, "N": 4, "W": 16},
    4: {"S": 3, "N": 5, "W": 15},
    5: {"S": 4, "N": 6, "W": 14},
    6: {"S": 5, "N": 7, "W": 13},
    7: {"S": 6, "N": 8, "W": 12},
    8: {"S": 7, "N": 9, "W": 11},
    9: {"S": 8, "W": 10},

    #right-hand rack endpoints, drop off points ie. bottom rack B
    10: {"E": 9},
    11: {"E": 8},
    12: {"E": 7},
    13: {"E": 6},
    14: {"E": 5},
    15: {"E": 4},

    #right-hand collection endpoints, pick up boxes ie. B
    16: {"E": 3},
    17: {"E": 2},

    #centre main line ie. top part
    19: {"S": 18, "N": 20, "W": 30, "E": 36},
    20: {"S": 19, "N": 21, "W": 29, "E": 35},
    21: {"S": 20, "N": 22, "W": 28, "E": 34},
    22: {"S": 21, "N": 23, "W": 27, "E": 33},
    23: {"S": 22, "N": 24, "W": 26, "E": 32},
    24: {"S": 23, "W": 25, "E": 31},

    #centre rack endpoints on the left side ie. top rack A
    25: {"E": 24},
    26: {"E": 23},
    27: {"E": 22},
    28: {"E": 21},
    29: {"E": 20},
    30: {"E": 19},

    #centre rack endpoints on the right side ie. top rack B
    31: {"W": 24},
    32: {"W": 23},
    33: {"W": 22},
    34: {"W": 21},
    35: {"W": 20},
    36: {"W": 19},

    #left-hand collection junctions, pick up boxes ie. A
    52: {"S": 54, "N": 53, "E": 38},
    53: {"S": 52, "N": 40, "E": 39},

    #left-hand collection endpoints ie. A
    38: {"W": 52},
    39: {"W": 53},

    #left-hand main line ie. A
    40: {"S": 53, "N": 41, "E": 51},
    41: {"S": 40, "N": 42, "E": 50},
    42: {"S": 41, "N": 43, "E": 49},
    43: {"S": 42, "N": 44, "E": 48},
    44: {"S": 43, "N": 45, "E": 47},
    45: {"S": 44, "E": 46},

    #left-hand rack endpoints, drop off ie. bottom rack A
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
#it then considers the nodes attached to those nodes and so on and so forth
#stops once it hits the target node

def find_path(mapping, curr_node, target):
    #mapping is your map dictionary
    #curr_node is the starting node
    #target is the node we want to reach

    #if we are already at the target, no travelling is needed, so return current node
    if curr_node == target:
        return [curr_node]

    #remember how we discovered each node
    #eg. parents[1] = 0 means we found node 1 from node 0 ie. 0 : 1
    #starting node has no parent
    parents = {curr_node: None}

    #create waiting list of nodes whose connections need checking
    #initially, only the starting node is waiting
    #ie. if queue is 0 1 2
    #0 connects to 1 and 2
    #1 connects to 3 4
    #2 connected to 5 6
    #thus queue is as follows
    #after 0 -> 1 2
    #after 1 -> 3 4 5
    #after 2 -> 3 4 5 6
    #these will be added to queue
    #note that 2 appears twice, so we must ensure 2 is not counted again when considering node 3, despite being attached to 3
    queue = [curr_node]

    #keep searching while there are nodes waiting in the queue.
    while queue:
        #remove the first waiting node and place it in node to check it next
        #pop(0) takes the FIRST item out of the list
        node = queue.pop(0)

        #look at every node connected to this node
        #.values() gives the node numbers, without the directions
        #for neightbour, means that for every node value attached to current node, is being considered
        for neighbour in mapping[node].values():

            #skip missing connections or nodes already discovered
            #prevents the search repeatedly going around loops
            if neighbour is None or neighbour in parents:
                #continue means it skips it and just moves onto next attaching node
                continue

            #remember which node led us to this neighbour
            #place this back into the parents list to keep track of route
            parents[neighbour] = node
            #essentialy parents[1] = 0, means that 0 will be added to node 1 route

            #if this neighbour is our target, rebuild the route
            if neighbour == target:

                #start the route list with the target
                #ie. the neighbour ie. the current node we have discovered ie. the target
                path = [neighbour]

                #path[-1] means the last node in the path list
                #keep adding its parent until we reach the start
                #it back tracks the route essentially
                #starting with target, we check its parent in the dictionary
                #we then set that parent as the new current mode and find its parent and so on
                #we add this to our path list
                while parents[path[-1]] is not None:
                    path.append(parents[path[-1]])

                #list currently runs from target back to start
                #reverse it so it runs from start to target
                return path[::-1]

            #if this is not the target, add it to the queue
            #so we can check its connections later
            #ensures we reset back to checking next value in list
            queue.append(neighbour)

    #if the queue becomes empty without finding the target,
    #there is no route to it.
    return None

#we now need to translate our path into the directions and instructions to follow
#start by defining function that finds direction between two nodes
def direction_between(curr_node, next_node):
    # look through the connections at the current node
    #first variable is the direction, and its attachement in the dictionary is the node
    #if we test each direction and see if its attachment is our target then that is our direction
    for direction, neighbour in mapping[curr_node].items():

        # return the compass direction leading to the next node
        if neighbour == next_node:
            return direction

    return None


#find what turn it corresponds to ie. N -> W is left 90 degrees
#heading is the way it currently is facing, wanted is the direction we want it to head
def get_turn(heading, wanted):
    directions= ["N", "E", "S", "W"]

    #we find the difference in direction between the heading and wanted 
    #we do this by seeing what our heading and wanted position  in our directions list is and feeding back its spot
    #by divding by 4, we get a corresponding number for what we want to do 
    #the % gives the remainder after the division
    # ie. N-> W is (0-3) / 4 means remainder 3
    difference_between= (directions.index(wanted) - directions.index(heading)) % 4

    #this means that 0 = go straight
    # 1 = go right
    # 2 = 180 u turn
    # 3 = left
    
    actions = ["straight", "right", "u_turn", "left"]
    #returns what action needs to be executed
    return actions[difference_between]


#calculation of move that needs to be done
def plan_move(curr_node, target, heading):
    # calculate the route
    path = find_path(mapping, curr_node, target)

    # no next move if no route exists or we are already there, we know we there is route is only 1 item
    if path is None or len(path) < 2:
        return None

    # find the next node and its compass direction
    next_node = path[1]
    #find the direction we want
    wanted = direction_between(curr_node, next_node)

    # calculate the physical turn
    action = get_turn(heading, wanted)

    #return our action, next node so we can update it, wanted so we can update direction
    return action, next_node, wanted

#assign important nodes to correct categroies
collection_nodes = {"A": [38, 39],  "B": [16, 17]}


storage_nodes = {
    "A_top": [25, 26, 27, 28, 29, 30],
    "A_bottom": [46, 47, 48, 49, 50, 51],
    "B_top": [31, 32, 33, 34, 35, 36],
    "B_bottom": [10, 11, 12, 13, 14, 15]}

home_node = 0

#when it reaaches an end point it at the drop off points it reads 0000
#create map of all these end points 
#storage endpoints expected to read 0000.
line_end_nodes = {
    10, 11, 12, 13, 14, 15,       # Bottom B
    25, 26, 27, 28, 29, 30,       # Top A
    31, 32, 33, 34, 35, 36,       # Top B
    46, 47, 48, 49, 50, 51}       # Bottom A


