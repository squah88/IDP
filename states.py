#create different states robot is in

def collecting():
    # Eventually:
    # 1. Choose a collection bay.
    # 2. Navigate there.
    # 3. Collect and identify the parcel.
    # Return True only when collection succeeds.
    return False


def checking_spaces():
    # Eventually:
    # 1. Navigate to a suitable storage space.
    # 2. Check occupancy.
    # 3. If occupied, choose another space.
    # Return True only when an empty space is confirmed.
    return False


def delivering():
    # Eventually operate the grabber to deposit the parcel.
    # Return True only when delivery succeeds.
    return False


def return_start():
    # Eventually navigate to node 0 and park.
    # Return True only when parked.
    return False
