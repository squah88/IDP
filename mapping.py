#creating map for each junction
#use breadth first search route planner to find the shortest route to node
#north is facing traffic lights at start
#make map for nodes - see google drive for drawing of map
#mapping[node] = {direction: neighbouring node}

mapping = {
    #start and start-box boundaries
    0:  {"N": 18, "E": 1, "W": 37},
    1:  {"W": 0, "E": 55},
    18: {"S": 0, "N": 19},
    37: {"E": 0, "W": 54},

    #bottom corners
    54: {"E": 37, "N": 52},
    55: {"W": 1, "N": 2},

    #right-hand main line (rack B side)
    2: {"S": 55, "N": 3, "W": 17},
    3: {"S": 2, "N": 4, "W": 16},
    4: {"S": 3, "N": 5, "W": 15},
    5: {"S": 4, "N": 6, "W": 14},
    6: {"S": 5, "N": 7, "W": 13},
    7: {"S": 6, "N": 8, "W": 12},
    8: {"S": 7, "N": 9, "W": 11},
    9: {"S": 8, "W": 10},

    #bottom rack B slots
    10: {"E": 9},
    11: {"E": 8},
    12: {"E": 7},
    13: {"E": 6},
    14: {"E": 5},
    15: {"E": 4},

    #rack B collection bays
    16: {"E": 3},
    17: {"E": 2},

    #centre main line between the top racks
    19: {"S": 18, "N": 20, "W": 30, "E": 36},
    20: {"S": 19, "N": 21, "W": 29, "E": 35},
    21: {"S": 20, "N": 22, "W": 28, "E": 34},
    22: {"S": 21, "N": 23, "W": 27, "E": 33},
    23: {"S": 22, "N": 24, "W": 26, "E": 32},
    24: {"S": 23, "W": 25, "E": 31},

    #top rack A slots
    25: {"E": 24},
    26: {"E": 23},
    27: {"E": 22},
    28: {"E": 21},
    29: {"E": 20},
    30: {"E": 19},

    #top rack B slots
    31: {"W": 24},
    32: {"W": 23},
    33: {"W": 22},
    34: {"W": 21},
    35: {"W": 20},
    36: {"W": 19},

    #rack A collection bays
    38: {"W": 52},
    39: {"W": 53},

    #left-hand main line (rack A side)
    52: {"S": 54, "N": 53, "E": 38},
    53: {"S": 52, "N": 40, "E": 39},
    40: {"S": 53, "N": 41, "E": 51},
    41: {"S": 40, "N": 42, "E": 50},
    42: {"S": 41, "N": 43, "E": 49},
    43: {"S": 42, "N": 44, "E": 48},
    44: {"S": 43, "N": 45, "E": 47},
    45: {"S": 44, "E": 46},

    #bottom rack A slots
    46: {"W": 45},
    47: {"W": 44},
    48: {"W": 43},
    49: {"W": 42},
    50: {"W": 41},
    51: {"W": 40}
}

def find_path(mapping, curr_node, target):
    #breadth first search: returns the shortest route from curr_node to target as a list of nodes
    #e.g. find_path(mapping, 0, 17) -> [0, 1, 55, 2, 17], or None if there is no route
    #it works by checking the start's neighbours first, then their neighbours, and so on
    #it remembers which node we found each node from (parents)
    #when we reach the target, follow the parents back to the start to get the route

    #already there
    if curr_node == target:
        return [curr_node]

    #eg. parents[1] = 0 means we found node 1 from node 0 ie. 0 : 1 (staart has no parent)
    parents = {curr_node: None}

    #queue = the waiting list of nodes whose connections still need checking
    #we always take the first node out and add its new neighbours to the end
    #eg: 0 connects to 1 and 2, 1 connects to 3, 2 connects to 3 and 4
    #  start           -> queue [0]
    #  take 0, add 1 2 -> queue [1, 2]
    #  take 1, add 3   -> queue [2, 3]
    #  take 2, add 4   -> queue [3, 4] (3 is skipped, we already found it from 1)
    #so nodes are checked in order of how far they are from the start, which gives the shortest route
    queue = [curr_node]

    #keep searching while there are nodes waiting in the queue
    while queue:
        #pop(0) takes the first item out of the list
        node = queue.pop(0)

        #look at every node connected to this one (.values() gives the node numbers without the directions)
        for neighbour in mapping[node].values():

            #skip nodes we've already found, so the search doesn't go round in loops
            if neighbour is None or neighbour in parents:
                continue            #skip to the next neighbour

            #remember which node led us here, e.g. parents[1] = 0 means we reached 1 from 0
            parents[neighbour] = node

            #found the target - rebuild the route by following the parents back to the start
            #e.g. with parents {0: None, 2: 0, 4: 2} and target 4:
            #[4] -> parent of 4 is 2 -> [4, 2] -> parent of 2 is 0 -> [4, 2, 0] -> 0 has no parent, stop
            if neighbour == target:
                path = [neighbour]

                #path[-1] is the last node in the list - keep adding its parent until we reach the start
                while parents[path[-1]] is not None:
                    path.append(parents[path[-1]])

                #the list runs target -> start, so reverse it to get start -> target, e.g. [0, 2, 4]
                return path[::-1]

            #not the target - add it to the end of the queue to check its connections later
            queue.append(neighbour)

    #the queue ran out without finding the target, so there is no route
    return None

def direction_between(curr_node, next_node):
    #turn the route into directions the robot can follow
    #e.g. mapping[2] = {"S": 55, "N": 3, "W": 17}, so direction_between(2, 17) -> "W"
    #.items() splits that into (direction, node) pairs: ("S", 55), ("N", 3), ("W", 17)
    #each time round the loop, direction = the letter and neighbour = the node number
    for direction, neighbour in mapping[curr_node].items():
        if neighbour == next_node:
            return direction

    return None

def get_turn(facing, wanted):
    #find which turn gets us from the way we're facing to the way we want to go
    directions = ["N", "E", "S", "W"]

    #count how many quarter turns CLOCKWISE we need, using each direction's position in the list
    #% 4 gives the remainder after dividing by 4, so the answer is always 0-3
    #e.g. facing N, want W: (3 - 0) % 4 = 3 -> left
    difference_between = (directions.index(wanted) - directions.index(facing)) % 4

    #0 = go straight
    #1 = go right
    #2 = 180 u turn
    #3 = left
    actions = ["straight", "right", "u_turn", "left"]
    return actions[difference_between]

def plan_move(curr_node, target, facing):
    #work out next move to make
    path = find_path(mapping, curr_node, target)

    #no route, or already there (a route of just 1 node means we're at the target)
    if path is None or len(path) < 2:
        return None

    #find the next node and its compass direction to work out which way to turn
    next_node = path[1]
    wanted = direction_between(curr_node, next_node)
    action = get_turn(facing, wanted)

    #navigation uses next_node and wanted to update where we are and which way we face
    return action, next_node, wanted

#collection bays for each rack
collection_nodes = {"A": [38, 39],  "B": [16, 17]}

#rack slots
storage_nodes = {
    "A_top": [25, 26, 27, 28, 29, 30],
    "A_bottom": [46, 47, 48, 49, 50, 51],
    "B_top": [31, 32, 33, 34, 35, 36],
    "B_bottom": [10, 11, 12, 13, 14, 15]}

home_node = 0 #the start box

#rack slots - the line ends there, so the sensors read 0000 when we arrive
line_end_nodes = {
    10, 11, 12, 13, 14, 15,       #bottom B
    25, 26, 27, 28, 29, 30,       #top A
    31, 32, 33, 34, 35, 36,       #top B
    46, 47, 48, 49, 50, 51}       #bottom A